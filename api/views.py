from rest_framework import viewsets, generics, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from orders.models import Order, OrderItem
from products.models import Product
from orders.cart import Cart
from reviews.models import Review
from .serializers import (
    ProductSerializer,
    ProductDetailSerializer,
    ReviewSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    UserRegisterSerializer
)


class ProductView(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/products/ - список товаров с пагинацией, фильтрацией и поиском list
    GET /api/products/{id}/ - детальная информация о товаре retrieve
    """
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related('reviews')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['price', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer



    @action(detail=True, methods=['get', 'post'], url_path='reviews', permission_classes=[AllowAny])
    def reviews(self, request, *args, **kwargs):
        product = self.get_object()
        if request.method == 'GET':
            reviews = Review.objects.filter(product=product)
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        bought = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status=Order.Status.DELIVERED
        ).exists()
        if not bought:
            return Response({'detail': 'You can only review products you have purchased'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')

    def create(self, request, *args, **kwargs):
        serialzier = OrderCreateSerializer(data=request.data)
        serialzier.is_valid(raise_exception=True)
        d = serialzier.validated_data
        cart = Cart(request)
        if len(cart) == 0:
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    total_price=cart.get_total_price(),
                    full_name=d['full_name'],
                    phone=d['phone'],
                    shipping_address=f"{d['city']}, {d['address']}",
                    status=Order.Status.PENDING,
                )
                for item in cart:
                    product = Product.objects.select_for_update().get(id=item['product'].id)
                    qty = item['quantity']
                    if product.stock < qty:
                        raise serializers.ValidationError(f'Not enough stock for "{product.name}"')
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        price=item['price'],
                    )
                    product.stock -= qty
                    product.save(update_fields=['stock'])
                cart.clear()
                serializer = OrderSerializer(order)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as exc:
            return Response({'detail': exc.detail}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()

        new_status = request.data.get('status')

        cancellable = {Order.Status.PENDING, Order.Status.PAID}
        if new_status == 'cancelled':
            if order.status not in cancellable:
                return Response({'detail': 'Order cannot be cancelled in its current status'}, status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic():
                for item in order.items.select_related('product'):
                    product = item.product
                    product.stock += item.quantity
                    product.save(update_fields=['stock'])
                order.status = Order.Status.CANCELLED
                order.save(update_fields=['status'])
                return Response({'detail': 'Order cancelled'}, status=status.HTTP_200_OK)

        return Response({'detail': 'Invalid status update'}, status=status.HTTP_400_BAD_REQUEST)



class CartAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def get(self, request, product_id=None):
        cart = Cart(request=request)
        data = []
        for item in cart:
            data.append({
                'product_id': item['product'].id,
                'name': item['product'].name,
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['quantity'] * item['price']
            })
        return Response({'items': data, 'total': cart.get_total_price()})

    def post(self, request, product_id=None):
        product_id = product_id or request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        cart = Cart(request=request)
        cart.add(product=product, quantity=quantity)
        return Response({'detail': 'Product added to cart'}, status=status.HTTP_200_OK)


    def delete(self, request, product_id=None):
        product_id = product_id or request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        cart = Cart(request=request)
        cart.remove(product=product)
        return Response({'detail': 'Product removed from cart'}, status=status.HTTP_200_OK)



class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]
