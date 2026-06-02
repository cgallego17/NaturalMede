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

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError('La cantidad debe ser mayor a 0.')
        return quantity

    def clean_unit_price(self):
        unit_price = self.cleaned_data.get('unit_price')
        if unit_price is not None and unit_price <= 0:
            raise forms.ValidationError('El precio unitario debe ser mayor a 0.')
        return unit_price

    def clean_discount_percentage(self):
        discount = self.cleaned_data.get('discount_percentage')
        if discount is not None and (discount < 0 or discount > 100):
            raise forms.ValidationError('El descuento debe estar entre 0 y 100.')
        return discount

