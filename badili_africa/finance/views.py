import os
import base64
import json
import requests
import re
import pytesseract
from PIL import Image
from io import BytesIO
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    parser_classes,
)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Expense, User, Project
from .serializers import (
    ExpenseSerializer,
    UserSerializer,
    ProjectSerializer,
    LoginSerializer,
)
from .authentication import BearerTokenAuthentication

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        # Get project name from request data
        project_name = self.request.data.get("project_name")

        # Find the first project with the given name
        project = Project.objects.filter(name=project_name).first()

        if not project:
            # Return an error if no project is found
            raise ValidationError({"error": "Project with the given name not found."})

        # Get the uploaded file from the request
        file = self.request.FILES.get("receipt", None)

        # Validate file size and type
        if file:
            self.validate_file(file)

        # Save the expense with the project_id and project officer details
        serializer.save(
            project_id=project,
            project_officer_id=self.request.user,
            project_officer=self.request.user.first_name,
        )

    def validate_file(self, file):
        # Check file size (limit 15MB)
        max_size_mb = 15
        if file.size > max_size_mb * 1024 * 1024:
            raise ValidationError({"error": f"File size exceeds {max_size_mb}MB."})

        # Check file extension
        allowed_extensions = [".pdf", ".doc", ".docx", ".odf", ".jpg", ".jpeg", ".png"]
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_extensions:
            raise ValidationError(
                {
                    "error": "Invalid file type. Allowed types: PDF, Word documents, or images."
                }
            )


class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                "token": token.key,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {"token": f"Bearer {token.key}", "user_id": user.pk, "email": user.email}
        )


@api_view(["GET"])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def get_expenses_by_project(request, project_id):
    expenses = Expense.objects.filter(project_id=project_id)
    serializer = ExpenseSerializer(expenses, many=True)
    return Response(serializer.data)


@api_view(["PATCH"])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def update_project_status(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    new_status = request.data.get("status", "").lower()

    # Validate the status
    if new_status not in ["inactive", "active", "completed", "abandoned"]:
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    # Update and save the new status
    project.status = new_status
    project.save()

    return Response(
        {
            "message": "Project status updated successfully",
            "project": ProjectSerializer(project).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_receipt_and_extract_data(request):
    # Get the uploaded file from the request
    file = request.FILES.get("receipt", None)
    if not file:
        return Response(
            {"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Validate file size and extension
    try:
        validate_file(file)
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Read the file content as an image
    try:
        image = Image.open(file)
    except Exception as e:
        return Response(
            {"error": "Invalid image format."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Use Tesseract to extract text from the image
    extracted_text = pytesseract.image_to_string(image)

    # Extract all relevant data from the text
    extracted_data = extract_receipt_data(extracted_text)

    # Return the result as JSON
    return Response(extracted_data, status=status.HTTP_200_OK)


def extract_receipt_data(text):
    # Initialize an array to hold all extracted items
    items = []

    # Define regex patterns to extract relevant fields
    item_pattern = re.compile(
        r"(?P<item_no>\d+)\s+(?P<product>[\w\s]+)\s+(?P<quantity>\d+)\s+(?P<unit_price>\d+\.\d{2})\s+(?P<subtotal>\d+\.\d{2})",
        re.IGNORECASE,
    )
    tax_pattern = re.compile(r"(?i)tax\s*[:\s]\s*\$?(\d+\.\d{2})")
    discount_pattern = re.compile(r"(?i)discount\s*[:\s]\s*\$?(\d+\.\d{2})")
    total_amount_pattern = re.compile(r"(?i)total\s*[:\s]\s*\$?(\d+\.\d{2})")

    # Iterate through each line of the receipt text and match expense items
    for match in item_pattern.finditer(text):
        item_no = match.group("item_no")
        product = match.group("product").strip()
        quantity = int(match.group("quantity"))
        unit_price = float(match.group("unit_price"))
        subtotal = float(match.group("subtotal"))

        # Add the matched item to the list
        items.append(
            {
                "Item No": item_no,
                "Product service": product,
                "Quantity": quantity,
                "Unit price": unit_price,
                "Subtotal": subtotal,
            }
        )

    # Extract the tax, discount, and total amount
    tax = tax_pattern.search(text)
    discount = discount_pattern.search(text)
    total_amount = total_amount_pattern.search(text)

    # Build the final JSON structure with all important details
    receipt_data = {
        "items": items,
        "tax": float(tax.group(1)) if tax else 0.00,
        "discount": float(discount.group(1)) if discount else 0.00,
        "total_amount": float(total_amount.group(1)) if total_amount else None,
        "description": extract_description(text),
    }

    return receipt_data


def extract_description(text):
    # Simple heuristic to get a description from the receipt (e.g., store name)
    # Here, we assume the store name might appear near the top of the receipt
    first_few_lines = text.split("\n")[:5]
    description = " ".join(line.strip() for line in first_few_lines if line.strip())
    return description


def validate_file(file):
    # Check file size (limit 15MB)
    max_size_mb = 15
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File size exceeds {max_size_mb}MB.")

    # Check file extension
    allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png"]
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError("Invalid file type. Allowed types: PDF or images.")
