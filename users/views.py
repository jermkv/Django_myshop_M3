
from django.views.generic import TemplateView, FormView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model, login
from .forms import SimpleRegisterForm, ProfileUpdateForm
from orders.models import Order

User = get_user_model()


class RegisterView(FormView):
    template_name = 'register.html'
    form_class = SimpleRegisterForm
    success_url = reverse_lazy('account')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = User.objects.create_user(username=email, email=email, password=password)
        login(self.request, user)
        return super().form_valid(form)


class AccountView(LoginRequiredMixin, TemplateView):
    template_name = 'account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = Order.objects.filter(user=self.request.user).prefetch_related('items__product')
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'profile_edit.html'
    success_url = reverse_lazy('account')

    def get_object(self, queryset=None):
        return self.request.user
