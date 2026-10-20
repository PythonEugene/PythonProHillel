from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import BookViewSet, CategoryViewSet, MeView, RegisterView, OrderViewSet, CartViewSet
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView, SpectacularRedocView

app_name = 'api'

router = DefaultRouter()
router.register('books', BookViewSet, basename='book')
router.register('categories', CategoryViewSet, basename='category')
router.register('orders', OrderViewSet, basename='order')
router.register('cart', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='docs'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('users/me/', MeView.as_view(), name='me'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
]
