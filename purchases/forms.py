from django import forms
from django.forms import inlineformset_factory
from .models import Purchase, PurchaseItem, Supplier, PurchaseReceipt
from catalog.models import Product


class SupplierForm(forms.ModelForm):
    """Formulario para proveedores"""
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'contact_person', 'email', 'phone', 
            'address', 'city', 'tax_id', 'payment_terms', 
            'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del proveedor'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Persona de contacto'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@proveedor.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+57 300 123 4567'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad'
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NIT/RUT'
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 30 días'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class PurchaseForm(forms.ModelForm):
    """Formulario para compras"""
    
    class Meta:
        model = Purchase
        fields = [
            'supplier', 'order_date', 'expected_delivery', 
            'status', 'payment_status', 'shipping_cost', 'notes'
        ]
        widgets = {
            'supplier': forms.Select(attrs={
                'class': 'form-control'
            }),
            'order_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expected_delivery': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'shipping_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas de la compra'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar proveedores activos
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)


class PurchaseItemForm(forms.ModelForm):
    """Formulario para items de compra"""
    
    class Meta:
        model = PurchaseItem
        fields = [
            'product', 'quantity', 'unit_cost', 
            'tax_percentage', 'discount_percentage'
        ]
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-control product-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '1',
                'value': '1'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'tax_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar productos activos
        self.fields['product'].queryset = Product.objects.filter(is_active=True)


# Formset para items de compra
PurchaseItemFormSet = inlineformset_factory(
    Purchase,
    PurchaseItem,
    form=PurchaseItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class PurchaseReceiptForm(forms.ModelForm):
    """Formulario para recibos de compra"""
    
    class Meta:
        model = PurchaseReceipt
        fields = ['receipt_number', 'notes']
        widgets = {
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de recibo'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas de recepción'
            })
        }
