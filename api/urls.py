from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductView, basename='product')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('cart/', views.CartAPIView.as_view(), name='api_cart'),
    path('cart/<int:product_id>/', views.CartAPIView.as_view(), name='api_cart_item'),
    path('auth/register/', views.UserRegisterView.as_view(), name='api_register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger_ui'),

]
