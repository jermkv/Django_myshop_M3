from decimal import Decimal
from products.models import Product

CART_SESSION_KEY = 'cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, product: Product, quantity: int = 1, override: bool = False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
                'name': product.name
            }

        if override:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        # Проверка остатка
        max_qty = product.stock
        if self.cart[product_id]['quantity'] > max_qty:
            self.cart[product_id]['quantity'] = max_qty

        self.save()

    def remove(self, product: Product | None = None, product_id: int | str | None = None) -> None:
        """
        Remove product from cart. Accepts either a Product instance or product_id.
        """
        if product is not None:
            key = str(product.id)
        elif product_id is not None:
            key = str(product_id)
        else:
            return

        if key in self.cart:
            del self.cart[key]
            self.save()

    def save(self) -> None:
        self.session.modified = True

    def clear(self) -> None:
        if CART_SESSION_KEY in self.session:
            del self.session[CART_SESSION_KEY]
            self.save()

    def get_total_price(self) -> int:
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product
        for item in cart.values():
            item['total_price'] = Decimal(item['price']) * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

