import os
import openai
from django.core.exceptions import ValidationError
from django.shortcuts import render , get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes , parser_classes
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Expense, User, Project
from .serializers import ExpenseSerializer, UserSerializer, ProjectSerializer, LoginSerializer
from .authentication import BearerTokenAuthentication

openai.api_key = os.getenv('OPENAI_API_KEY')

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
        project_name = self.request.data.get('project_name')

        # Find the first project with the given name
        project = Project.objects.filter(name=project_name).first()

        if not project:
            # Return an error if no project is found
            raise ValidationError({"error": "Project with the given name not found."})

        # Get the uploaded file from the request
        file = self.request.FILES.get('receipt', None)
        
        # Validate file size and type
        if file:
            self.validate_file(file)

        # Save the expense with the project_id and project officer details
        serializer.save(
            project_id=project,
            project_officer_id=self.request.user,
            project_officer=self.request.user.first_name
        )

    def validate_file(self, file):
        # Check file size (limit 15MB)
        max_size_mb = 15
        if file.size > max_size_mb * 1024 * 1024:
            raise ValidationError({"error": f"File size exceeds {max_size_mb}MB."})

        # Check file extension
        allowed_extensions = ['.pdf', '.doc', '.docx', '.odf', '.jpg', '.jpeg', '.png']
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_extensions:
            raise ValidationError({"error": "Invalid file type. Allowed types: PDF, Word documents, or images."})


class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key
        }, status=status.HTTP_201_CREATED)

class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': f'Bearer {token.key}',
            'user_id': user.pk,
            'email': user.email
        })

@api_view(['GET'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def get_expenses_by_project(request, project_id):
    expenses = Expense.objects.filter(project_id=project_id)
    serializer = ExpenseSerializer(expenses, many=True)
    return Response(serializer.data)

@api_view(['PATCH'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def update_project_status(request, project_name):
    project = get_object_or_404(Project, name=project_name)
    new_status = request.data.get('status', '').lower()

    # Validate the status
    if new_status not in ['inactive', 'active', 'completed', 'abandoned']:
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    # Update and save the new status
    project.status = new_status
    project.save()

    return Response({
        "message": "Project status updated successfully",
        "project": ProjectSerializer(project).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_receipt_and_extract_data(request):
    # Get the uploaded file from the request
    file = request.FILES.get('receipt', None)

    if not file:
        return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    # Validate file size and extension (as per the previous example)
    try:
        validate_file(file)
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Send the file to GPT-4 for processing
    try:
        receipt_data = process_receipt_with_gpt(file)
        return Response(receipt_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def validate_file(file):
    # Check file size (limit 15MB)
    max_size_mb = 15
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File size exceeds {max_size_mb}MB.")

    # Check file extension
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError("Invalid file type. Allowed types: PDF or images.")


def process_receipt_with_gpt(file_content):
    # Make a request to GPT-4 with the custom function call for receipts
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a system that processes receipts and extracts key details."
            },
            {
                "role": "user",
                "content": "Here is a receipt. Please extract the total amount and description.",
                "files": {"receipt": file_content}
            }
        ],
        functions=[
            {
                "name": "extract_receipt_data",
                "description": "Extracts the total amount and description from a receipt.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "number",
                            "description": "The total amount on the receipt."
                        },
                        "description": {
                            "type": "string",
                            "description": "A brief description of the receipt."
                        }
                    },
                    "required": ["amount", "description"]
                }
            }
        ],
        response_format={"type" : "json_object"},
        function_call={"name": "extract_receipt_data"}
    )

    # Process the response from GPT-4
    function_result = response.get("choices")[0].get("message").get("function_call").get("arguments")

    if function_result:
        # Parse the result
        receipt_data = function_result
        return {
            "amount": receipt_data.get("amount"),
            "description": receipt_data.get("description")
        }
    else:
        return {"error": "file is not receipt"}