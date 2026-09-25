from django.contrib import admin
from .models import (
    Brand, Product, Dealer, Visit, ProductAwareness,
    PriceComparison, Turnover, ProjectVisit, Notification,
)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand_type', 'market_strength', 'is_active')
    list_filter = ('brand_type', 'market_strength', 'is_active')
    search_fields = ('name', 'contact_person')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'unit_price', 'is_active')
    list_filter = ('brand', 'category', 'is_active')
    search_fields = ('name', 'sku')


@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_name', 'area', 'counter_type', 'phone', 'is_active', 'created_at')
    list_filter = ('area', 'counter_type', 'is_active')
    search_fields = ('name', 'owner_name', 'phone', 'address', 'contact_person')
    filter_horizontal = ('brands_dealt', 'products_dealt', 'assigned_salesmen')


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('salesman', 'dealer', 'check_in_time', 'check_out_time', 'duration_display')
    list_filter = ('salesman', 'dealer__area')
    search_fields = ('salesman__username', 'dealer__name')
    date_hierarchy = 'check_in_time'


@admin.register(ProductAwareness)
class ProductAwarenessAdmin(admin.ModelAdmin):
    list_display = ('dealer', 'product', 'is_in_stock', 'display_quality', 'recorded_by', 'recorded_at')
    list_filter = ('is_in_stock', 'display_quality')
    search_fields = ('dealer__name', 'product__name')


@admin.register(PriceComparison)
class PriceComparisonAdmin(admin.ModelAdmin):
    list_display = ('dealer', 'our_product', 'our_price', 'our_discount_percent',
                     'competitor_product', 'competitor_price', 'competitor_discount_percent', 'recorded_at')
    list_filter = ('dealer__area',)
    search_fields = ('dealer__name', 'our_product__name', 'competitor_product__name')


@admin.register(Turnover)
class TurnoverAdmin(admin.ModelAdmin):
    list_display = ('salesman', 'dealer', 'brand', 'product', 'amount', 'date')
    list_filter = ('date', 'salesman', 'brand')
    search_fields = ('dealer__name',)
    date_hierarchy = 'date'


@admin.register(ProjectVisit)
class ProjectVisitAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'salesman', 'project_type', 'stage', 'expected_business_value', 'visit_date')
    list_filter = ('stage', 'project_type', 'area')
    search_fields = ('project_name', 'location', 'contact_person')
    date_hierarchy = 'visit_date'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('title', 'recipient__username')
