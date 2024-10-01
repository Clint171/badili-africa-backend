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
    # Initialize a dictionary to hold the extracted data
    data = {
        "Item No": None,
        "Product service": None,
        "Quantity": None,
        "Unit price": None,
        "Subtotal": None,
        "tax": None,
        "discount": None,
        "amount": None,
        "description": None,
    }

    # Example regex patterns to extract relevant fields
    item_no_pattern = re.compile(r"Item No:\s*(\d+)")
    product_pattern = re.compile(r"Product service:\s*([\w\s-]+)")
    quantity_pattern = re.compile(r"Quantity:\s*(\d+)")
    unit_price_pattern = re.compile(r"Unit price:\s*\$?(\d+(\.\d{2})?)")
    subtotal_pattern = re.compile(r"Subtotal:\s*\$?(\d+(\.\d{2})?)")
    tax_pattern = re.compile(r"tax:\s*\$?(\d+(\.\d{2})?)")
    discount_pattern = re.compile(r"discount:\s*\$?(\d+(\.\d{2})?)")
    amount_pattern = re.compile(r"amount:\s*\$?(\d+(\.\d{2})?)")
    description_pattern = re.compile(r"description:\s*(.*)")

    # Extract data using regex patterns
    if match := item_no_pattern.search(text):
        data["Item No"] = match.group(1)
    if match := product_pattern.search(text):
        data["Product service"] = match.group(1).strip()
    if match := quantity_pattern.search(text):
        data["Quantity"] = int(match.group(1))
    if match := unit_price_pattern.search(text):
        data["Unit price"] = float(match.group(1))
    if match := subtotal_pattern.search(text):
        data["Subtotal"] = float(match.group(1))
    if match := tax_pattern.search(text):
        data["tax"] = float(match.group(1))
    if match := discount_pattern.search(text):
        data["discount"] = float(match.group(1))
    if match := amount_pattern.search(text):
        data["amount"] = float(match.group(1))
    if match := description_pattern.search(text):
        data["description"] = match.group(1).strip()

    return data


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
