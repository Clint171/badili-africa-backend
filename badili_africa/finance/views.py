from django.shortcuts import render , get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Expense, User, Project
from .serializers import ExpenseSerializer, UserSerializer, ProjectSerializer, LoginSerializer
from .authentication import BearerTokenAuthentication

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
        serializer.save(created_by=self.request.user)

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
    expenses = Expense.objects.filter(project=project_id)
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