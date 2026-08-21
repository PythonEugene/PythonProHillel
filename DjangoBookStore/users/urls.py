from django.urls import path
from .views import ManagerUserPermissionsView, RegisterView, CustomLogoutView, CustomLoginView

app_name = 'users'

urlpatterns = [
    path('manage/<int:user_id>/', ManagerUserPermissionsView.as_view(), name='manage_permissions'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]