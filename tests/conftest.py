import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.sessions.backends.db import SessionStore
from rest_framework.test import APIClient
from orders.models import Order, OrderItem
from products.models import Category, Product
from reviews.models import Review

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        password='superkey123',
        email='test@inbox.com'
    )

@pytest.fixture
def auth_client(api_client, user) -> APIClient:
    response = api_client.post('/api/v1/auth/login/', {
        'username': 'testuser',
        'password': 'superkey123'
    })
    token = response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
    return api_client


@pytest.fixture
def category(db) -> Category:
    return Category.objects.create(name='Hops', slug='hops')


@pytest.fixture
def product(db, category) -> Product:
    return Product.objects.create(
        name='Citra Hops',
        slug='citra-hops',
        description='Best hops',
        price=Decimal('5.99'),
        category=category,
        stock=100,
        is_active=True
    )


@pytest.fixture
def order(db, user, product) -> Order:
    o = Order.objects.create(
        user=user,
        total_price=Decimal('29.95'),
        full_name='Test User',
        phone='+1234567890',
        shipping_address='City, Street 1',
        status=Order.Status.PENDING,
    )
    OrderItem.objects.create(order=o, product=product, quantity=5, price=product.price)
    return o


@pytest.fixture
def review(db, user, product) -> Review:
    return Review.objects.create(
        user=user,
        product=product,
        rating=4,
        comment='Great hops for brewing!'
    )


@pytest.fixture
def mock_request(db):
    request = RequestFactory().get('/')
    request.session = SessionStore()
    request.session.create()
    return request