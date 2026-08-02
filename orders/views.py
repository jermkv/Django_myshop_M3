from django.views import View
from django.views.generic import TemplateView, DetailView
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from .cart import Cart
from products.models import Product
from .forms import CheckoutForm
from django.db import transaction
from .models import Order, OrderItem
from django.core.mail import send_mail
from django.conf import settings



class CartAddView(View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, is_active=True)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            messages.error(request, 'Укажите корректное количество товара')
            return redirect('products:detail', slug=product.slug)

        if quantity < 1 or quantity > product.stock:
            messages.error(request, f'Недопустимое кол-во. В наличии {product.stock} шт')
            return redirect('products:detail', slug=product.slug)

        cart = Cart(request)
        cart.add(product=product, quantity=quantity)
        messages.success(request, f'{product.name} добавлен в корзину')
        return redirect('cart')


class CartRemoveView(View):
    def post(self, request, product_id):
        cart = Cart(request)
        cart.remove(product_id=product_id)
        return redirect('cart')



class CartView(TemplateView):
    template_name = 'orders/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        context['cart'] = cart
        context['total'] = cart.get_total_price()
        return context



class CheckoutView(LoginRequiredMixin, View):
    """
    GET - /ordes/checkout/ - показывается форма
    POST - orders/checkout/ - создается заказ
    """

    @staticmethod
    def render_checkout(request, form, cart, status=200):
        return render(
            request,
            'orders/checkout.html',
            {
                'form': form,
                'cart': cart,
                'total': cart.get_total_price(),
            },
            status=status,
        )

    def get(self, request):
        cart = Cart(request=request)
        if len(cart) == 0:
            messages.warning(request, 'Корзина пуста')
            return redirect('cart')
        form = CheckoutForm()
        return self.render_checkout(request, form, cart)

    def post(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            messages.warning(request, 'Корзина пуста')
            return redirect('cart')

        form = CheckoutForm(request.POST)
        if not form.is_valid():
            return self.render_checkout(request, form, cart, status=400)

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    total_price=cart.get_total_price(),
                    full_name=form.cleaned_data['full_name'],
                    phone=form.cleaned_data['phone'],
                    shipping_address=f"{form.cleaned_data['city']}, {form.cleaned_data['address']}",
                    status=Order.Status.PENDING,
                )

                for item in cart:
                    product = Product.objects.select_for_update().get(id=item['product'].id)
                    qty = item['quantity']

                    if product.stock < qty:
                        raise ValidationError(f'Недостаточно товара "{product.name}" на складе')

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        price=item['price'],
                    )

                    product.stock -= qty
                    product.save(update_fields=['stock'])
        except ValidationError as exc:
            messages.error(request, exc.message)
            return self.render_checkout(request, form, cart, status=400)

        cart.clear()

        self.send_confirmation_email(order)
        messages.success(request, f'Заказ {order.id} оформлен')
        return redirect('success', order_id=order.id)

    def send_confirmation_email(self, order: Order) -> None:
        subject = f'Заказ {str(order.id)} принят - Hop & Barley'
        message = (
            f"Здравствуйте, {order.full_name}\n\n"
            f"Ваш заказ {str(order.id)} на сумму {order.total_price} принят\n"
            f"Адрес доставки {order.shipping_address}\n\n"
            f"Мы свяжемся с вами по номеру {order.phone}\n\nHop & Barley"
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.user.email])
        
        #Отправить сообщение администратору
        admin_subject = f'Новый заказ #{order.id}'
        admin_message = f'Поступил новый заказ #{order.id} от {order.full_name} на сумму {order.total_price}.'
        if hasattr(settings, 'ADMIN_EMAIL'):
            send_mail(admin_subject, admin_message, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_EMAIL])



class OrderSuccessView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/success.html'
    context_object_name = 'order'

    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')
