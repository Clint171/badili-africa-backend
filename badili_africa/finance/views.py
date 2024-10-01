import os
import base64
import json
import fitz
import requests
import re
import pytesseract
from PIL import Image
from io import BytesIO
from pdf2image import convert_from_path
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


# Function to validate the file (this can be customized based on size and extension)
def validate_file(file):
    max_file_size = 10 * 1024 * 1024  # 10 MB limit
    allowed_extensions = ["jpg", "jpeg", "png", "pdf"]
    file_extension = file.name.split(".")[-1].lower()

    if file.size > max_file_size:
        raise ValidationError(f"File size exceeds {max_file_size} bytes.")

    if file_extension not in allowed_extensions:
        raise ValidationError(f"Unsupported file extension: {file_extension}")


# Function to extract text from image files (png, jpg, jpeg)
def extract_text_from_image(image_file):
    image = Image.open(image_file)
    return pytesseract.image_to_string(image)

# Function to extract text from PDFs by converting PDF pages to images
def extract_text_from_pdf(pdf_file):
    # Convert PDF to images (1 image per page)
    pages = convert_from_path(pdf_file)
    extracted_text = ""
    for page in pages:
        text = pytesseract.image_to_string(page)
        extracted_text += text + "\n"
    return extracted_text

# Define the description extraction function
def extract_description(text):
    description_pattern = re.compile(r'(invoice|due date|company name|billed to)', re.IGNORECASE)
    for line in text.split('\n'):
        if description_pattern.search(line):
            return line.strip()
    return "No description available"

# Function to extract receipt details
def extract_receipt_data(text):
    items = []
    item_pattern = re.compile(
        r'(?P<product>[A-Za-z\s]+)\s+(?P<quantity>\d+)\s+(?P<unit_price>\d+\.\d{2})\s+(?P<subtotal>\d+\.\d{2})',
        re.IGNORECASE
    )
    tax_pattern = re.compile(r'(?i)(tax|vat|gst)\s*[:\s]\s*\$?(\d+\.\d{2})')
    discount_pattern = re.compile(r'(?i)(discount|savings)\s*[:\s]\s*\$?(\d+\.\d{2})')
    total_amount_pattern = re.compile(r'(?i)(total|grand total|amount due)\s*[:\s]\s*\$?(\d+\.\d{2})')

    for match in item_pattern.finditer(text):
        product = match.group("product").strip()
        quantity = int(match.group("quantity"))
        unit_price = float(match.group("unit_price"))
        subtotal = float(match.group("subtotal"))

        items.append({
            "Product service": product,
            "Quantity": quantity,
            "Unit price": unit_price,
            "Subtotal": subtotal
        })

    tax = tax_pattern.search(text)
    discount = discount_pattern.search(text)
    total_amount = total_amount_pattern.search(text)

    return {
        "items": items if items else "No items found",
        "tax": float(tax.group(2)) if tax else 0.00,
        "discount": float(discount.group(2)) if discount else 0.00,
        "total_amount": float(total_amount.group(2)) if total_amount else None,
        "description": extract_description(text)
    }

# Main API view to upload and extract receipt data
@api_view(["POST"])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_receipt_and_extract_data(request):
    file = request.FILES.get("receipt", None)
    if not file:
        return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    # Validate file extension and size
    try:
        validate_file(file)
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    file_extension = file.name.split('.')[-1].lower()

    # Check file type and extract text accordingly
    if file_extension in ['png', 'jpg', 'jpeg']:
        try:
            extracted_text = extract_text_from_image(file)
        except Exception as e:
            return Response({"error": "Could not process the image file."}, status=status.HTTP_400_BAD_REQUEST)
    elif file_extension == 'pdf':
        try:
            extracted_text = extract_text_from_pdf(file)
        except Exception as e:
            return Response({"error": "Could not process the PDF file."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "Unsupported file format."}, status=status.HTTP_400_BAD_REQUEST)

    # Extract receipt details from the extracted text
    extracted_data = extract_receipt_data(extracted_text)

    return Response(extracted_data, status=status.HTTP_200_OK)
