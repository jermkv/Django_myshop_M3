import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from products.models import Product
from products.models import Category
from django.contrib.auth import get_user_model

User = get_user_model()


def test_order_creation_via_api(auth_client, user, product):
    # Ensure cart is empty and add product via API
    response = auth_client.post('/api/v1/cart/', {'product_id': product.id, 'quantity': 2})
    assert response.status_code == 200

    # Create order with required fields
    payload = {
        'full_name': 'API User',
        'phone': '+10000000000',
        'city': 'City',
        'address': 'Street 1',
        'payment_method': 'card'
    }
    response = auth_client.post('/api/v1/orders/', payload)
    assert response.status_code == 201, response.content
    data = response.json()
    assert data['full_name'] == 'API User'
    assert data['total_price'] == str(Decimal(product.price) * 2)


def test_order_requires_auth(api_client, product):
    # Unauthenticated user cannot create order
    api_client.post('/api/v1/cart/', {'product_id': product.id, 'quantity': 1})
    response = api_client.post('/api/v1/orders/', {
        'full_name': 'Anon',
        'phone': '+100',
        'city': 'C',
        'address': 'A',
        'payment_method': 'card'
    })
    assert response.status_code in (401, 403)


def test_api_schema_and_docs(api_client):
    # Schema and docs should be accessible
    r_schema = api_client.get('/api/v1/schema/')
    r_docs = api_client.get('/api/v1/docs/')
    assert r_schema.status_code == 200
    assert r_docs.status_code == 200
