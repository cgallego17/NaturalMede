from django import forms
from django.forms import inlineformset_factory
from inventory.models import StockTransfer, StockTransferItem, Warehouse, Stock
from catalog.models import Product


class StockTransferForm(forms.ModelForm):
    """Formulario para crear transferencias de stock"""
    
    class Meta:
        model = StockTransfer
        fields = ['from_warehouse', 'to_warehouse', 'reference', 'notes']
        widgets = {
            'from_warehouse': forms.Select(attrs={'class': 'form-control'}),
            'to_warehouse': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Transferencia Enero 2024'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas adicionales...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['from_warehouse'].queryset = Warehouse.objects.filter(is_active=True)
        self.fields['to_warehouse'].queryset = Warehouse.objects.filter(is_active=True)
        self.fields['from_warehouse'].label = 'Bodega Origen'
        self.fields['to_warehouse'].label = 'Bodega Destino'
        self.fields['reference'].label = 'Referencia'
        self.fields['notes'].label = 'Notas'
    
    def clean(self):
        cleaned_data = super().clean()
        from_warehouse = cleaned_data.get('from_warehouse')
        to_warehouse = cleaned_data.get('to_warehouse')
        
        if from_warehouse and to_warehouse and from_warehouse == to_warehouse:
            raise forms.ValidationError('La bodega origen y destino deben ser diferentes')
        
        return cleaned_data


class StockTransferItemForm(forms.ModelForm):
    """Formulario para items de transferencia"""
    
    class Meta:
        model = StockTransferItem
        fields = ['product', 'quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notas del producto...'}),
        }
    
    def __init__(self, *args, **kwargs):
        warehouse_id = kwargs.pop('warehouse_id', None)
        super().__init__(*args, **kwargs)
        
        if warehouse_id:
            # Solo mostrar productos que tienen stock en la bodega origen
            products_with_stock = Product.objects.filter(
                stock__warehouse_id=warehouse_id,
                stock__quantity__gt=0,
                is_active=True
            ).distinct().order_by('name')
            self.fields['product'].queryset = products_with_stock
        
        self.fields['product'].label = 'Producto'
        self.fields['quantity'].label = 'Cantidad'
        self.fields['notes'].label = 'Notas'
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise forms.ValidationError('La cantidad debe ser mayor a 0')
        return quantity


# Formset para múltiples items de transferencia
StockTransferItemFormSet = inlineformset_factory(
    StockTransfer,
    StockTransferItem,
    form=StockTransferItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class StockTransferItemFormWithStock(StockTransferItemForm):
    """Formulario de item con información de stock disponible"""
    
    def __init__(self, *args, **kwargs):
        warehouse_id = kwargs.pop('warehouse_id', None)
        super().__init__(*args, **kwargs)
        
        if warehouse_id:
            # Agregar información de stock disponible
            products_with_stock = Product.objects.filter(
                stock__warehouse_id=warehouse_id,
                stock__quantity__gt=0,
                is_active=True
            ).distinct().order_by('name')
            
            # Crear choices con información de stock
            choices = []
            for product in products_with_stock:
                try:
                    stock = Stock.objects.get(product=product, warehouse_id=warehouse_id)
                    choices.append((product.id, f"{product.name} (Stock: {stock.quantity})"))
                except Stock.DoesNotExist:
                    continue
            
            self.fields['product'].widget = forms.Select(attrs={'class': 'form-control'})
            self.fields['product'].choices = choices


# Formset con información de stock
StockTransferItemFormSetWithStock = inlineformset_factory(
    StockTransfer,
    StockTransferItem,
    form=StockTransferItemFormWithStock,
    extra=0,  # Sin formularios iniciales
    can_delete=True,
    min_num=0,  # Permitir cero productos inicialmente
    validate_min=False  # Validación manual
)
