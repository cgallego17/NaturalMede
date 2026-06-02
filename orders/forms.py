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

    def clean(self):
        cleaned_data = super().clean()
        subtotal = cleaned_data.get('subtotal')
        iva_amount = cleaned_data.get('iva_amount')
        shipping_cost = cleaned_data.get('shipping_cost')
        total = cleaned_data.get('total')
        
        if all([subtotal is not None, iva_amount is not None, shipping_cost is not None, total is not None]):
            expected_total = subtotal + iva_amount + shipping_cost
            if abs(total - expected_total) > 0.01:
                self.add_error('total', f'El total debe ser {expected_total:.2f} (subtotal + IVA + envío).')
        
        return cleaned_data


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

    def clean(self):
        cleaned_data = super().clean()
        min_weight = cleaned_data.get('min_weight')
        max_weight = cleaned_data.get('max_weight')
        
        if min_weight is not None and max_weight is not None:
            if min_weight >= max_weight:
                raise forms.ValidationError('El peso mínimo debe ser menor que el peso máximo.')
        
        return cleaned_data













