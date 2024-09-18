from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from finance import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'expenses', views.ExpenseViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/projects/<int:project_id>/expenses/', views.get_expenses_by_project, name='expenses-by-project'),
    path('api/signup/', views.SignupView.as_view(), name='signup'),
    path('api/login/', views.LoginView.as_view(), name='api_login'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 