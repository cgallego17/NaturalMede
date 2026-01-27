from django import forms
from .models import Order, ShippingRate
from customers.models import Customer


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'customer', 'status', 'payment_method', 'subtotal', 'iva_amount',
            'shipping_cost', 'total', 'shipping_address', 'shipping_city',
            'shipping_phone', 'shipping_notes', 'notes', 'internal_notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'iva_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'shipping_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)


class ShippingRateForm(forms.ModelForm):
    class Meta:
        model = ShippingRate
        fields = ['city', 'min_weight', 'max_weight', 'cost', 'estimated_days', 'is_active']
        widgets = {
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'min_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'max_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }













