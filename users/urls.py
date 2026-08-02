from django.urls import path
from .views import RegisterView, AccountView, ProfileUpdateView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('account/', AccountView.as_view(), name='account'),
    path('account/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('account/password/', auth_views.PasswordChangeView.as_view(template_name='password_change.html', success_url='/account/'), name='password_change'),
]

