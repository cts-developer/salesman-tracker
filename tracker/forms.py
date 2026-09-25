from django import forms

from accounts.models import User, Area
from .models import (
    Dealer, Visit, ProductAwareness, PriceComparison,
    Turnover, ProjectVisit, Brand, Product,
)


BASE_WIDGET_ATTRS = {'class': 'form-control'}
SELECT_ATTRS = {'class': 'form-select'}
CHECK_ATTRS = {'class': 'form-check-input'}


class StyledModelForm(forms.ModelForm):
    """Applies Bootstrap classes to all fields automatically."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.update(SELECT_ATTRS)
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.update(CHECK_ATTRS)
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({**BASE_WIDGET_ATTRS, 'rows': 3})
            else:
                widget.attrs.update(BASE_WIDGET_ATTRS)


class AreaForm(StyledModelForm):
    class Meta:
        model = Area
        fields = ['name', 'code', 'city', 'state', 'description', 'is_active']


class DealerForm(StyledModelForm):
    """Dealer == Counter: this single form covers dealer info, location,
    counter type/GPS and salesmen assignment."""

    class Meta:
        model = Dealer
        fields = [
            'name', 'owner_name', 'contact_person', 'phone', 'email', 'area',
            'address', 'counter_type', 'latitude', 'longitude',
            'brands_dealt', 'products_dealt', 'assigned_salesmen',
            'gst_number', 'is_active',
        ]
        widgets = {
            'brands_dealt': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
            'products_dealt': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
            'assigned_salesmen': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
            'latitude': forms.NumberInput(attrs={'step': 'any', 'readonly': 'readonly'}),
            'longitude': forms.NumberInput(attrs={'step': 'any', 'readonly': 'readonly'}),
        }


class CheckInForm(StyledModelForm):
    class Meta:
        model = Visit
        fields = ['dealer', 'check_in_lat', 'check_in_lng', 'notes', 'photo']
        widgets = {
            'check_in_lat': forms.HiddenInput(),
            'check_in_lng': forms.HiddenInput(),
        }


class CheckOutForm(StyledModelForm):
    class Meta:
        model = Visit
        fields = ['check_out_lat', 'check_out_lng', 'notes']
        widgets = {
            'check_out_lat': forms.HiddenInput(),
            'check_out_lng': forms.HiddenInput(),
        }


class ProductAwarenessForm(StyledModelForm):
    class Meta:
        model = ProductAwareness
        fields = ['dealer', 'product', 'is_in_stock', 'stock_quantity_estimate',
                  'display_quality', 'is_visible_to_customer', 'photo', 'remarks']


class PriceComparisonForm(StyledModelForm):
    class Meta:
        model = PriceComparison
        fields = ['dealer', 'our_product', 'our_price', 'our_discount_percent',
                  'competitor_product', 'competitor_price', 'competitor_discount_percent',
                  'remarks']


class TurnoverForm(StyledModelForm):
    """Quantity removed; 'counter' replaced by 'brand' (dealer & counter are
    now the same entity, selected via the 'dealer' field)."""

    class Meta:
        model = Turnover
        fields = ['dealer', 'brand', 'product', 'amount', 'date', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].required = False
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['brand'].required = True


class ProjectVisitForm(StyledModelForm):
    class Meta:
        model = ProjectVisit
        fields = ['project_name', 'project_type', 'area', 'location', 'contact_person',
                  'contact_phone', 'stage', 'expected_business_value', 'visit_date',
                  'expected_closure_date', 'notes', 'photo']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expected_closure_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class BrandForm(StyledModelForm):
    """Includes competitor details, shown/used when Brand Type = Competitor."""

    class Meta:
        model = Brand
        fields = ['name', 'brand_type', 'logo', 'is_active',
                  'contact_person', 'contact_phone', 'market_strength', 'notes']


class ProductForm(StyledModelForm):
    class Meta:
        model = Product
        fields = ['brand', 'name', 'sku', 'category', 'unit_price', 'is_active']
