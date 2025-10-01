from django import forms
from .models import POSSale, POSSaleItem
from customers.models import Customer
from catalog.models import Product


class POSSaleForm(forms.ModelForm):
    class Meta:
        model = POSSale
        fields = ['order_type', 'customer', 'payment_method', 'notes']
        widgets = {
            'order_type': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
        self.fields['customer'].required = False


class POSSaleItemForm(forms.ModelForm):
    class Meta:
        model = POSSaleItem
        fields = ['product', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)

