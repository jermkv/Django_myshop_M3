from django.contrib import admin
from django.db.models import Avg
from .models import Category, Product
from rangefilter.filters import (
    NumericRangeFilter
)

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'created_at', 'product_count']
    
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_filter = ['parent', 'created_at']
    readonly_fields = ['created_at', 'updated_at']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Количество товаров'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'is_active', 'stock', 'created_at', 'average_rating']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_filter = ['category', 'is_active',('stock', NumericRangeFilter), 'created_at']
    readonly_fields = ['created_at', 'updated_at']

    def average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(reviews.aggregate(Avg('rating'))['rating__avg'], 1)
        return 'Нет отзывов'
    average_rating.short_description = 'Средний рейтинг'

