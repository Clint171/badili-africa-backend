from django.urls import include, path
from rest_framework import routers
from finance import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'expenses', views.ExpenseSourceViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/projects/<int:project_id>/expenses/', views.get_expenses_by_project, name='expenses-by-project'),
]
