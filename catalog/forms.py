from django import forms
from .models import Product, Category, Brand
from customers.models import City, Country, Department


class CartAddForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '99'
        })
    )


class CheckoutForm(forms.Form):
    PAYMENT_METHODS = [
        ('wompi', 'Wompi - Tarjeta de Crédito/Débito'),
    ]

    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Teléfono'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Dirección completa',
            'rows': 3
        })
    )

    country = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by('name'),
        empty_label='Selecciona país',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        empty_label='Selecciona departamento',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.none(),
        empty_label='Selecciona ciudad',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        initial='wompi',
        widget=forms.HiddenInput()  # Oculto porque solo hay una opción
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notas adicionales (opcional)',
            'rows': 3
        })
    )

    create_account = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        data = self.data if self.is_bound else None
        country = None
        department = None

        if data:
            try:
                country_id = int(data.get('country') or 0)
                if country_id:
                    country = Country.objects.filter(id=country_id).first()
            except (TypeError, ValueError):
                country = None

            try:
                department_id = int(data.get('department') or 0)
                if department_id:
                    department = Department.objects.filter(id=department_id).first()
            except (TypeError, ValueError):
                department = None

        if country:
            self.fields['department'].queryset = Department.objects.filter(
                country=country
            ).order_by('name')
        else:
            self.fields['department'].queryset = Department.objects.none()

        if department:
            self.fields['city'].queryset = City.objects.filter(
                department=department
            ).order_by('name')
        else:
            self.fields['city'].queryset = City.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        create_account = bool(cleaned_data.get('create_account'))
        password1 = cleaned_data.get('password1') or ''
        password2 = cleaned_data.get('password2') or ''

        if create_account:
            if not password1 or not password2:
                raise forms.ValidationError('Debes ingresar y confirmar una contraseña para crear tu cuenta.')
            if password1 != password2:
                raise forms.ValidationError('Las contraseñas no coinciden.')

        return cleaned_data


class ProductForm(forms.ModelForm):
    """Formulario para crear y editar productos"""
    
    # Campo para imagen principal
    main_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label="Imagen Principal"
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'description', 'short_description', 'category', 'brand', 
            'price', 'cost_price', 'iva_percentage', 'barcode', 'weight', 'dimensions', 'is_active', 'is_featured'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SKU del producto'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del producto',
                'rows': 4
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción corta del producto (máx. 300 caracteres)',
                'maxlength': '300'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'brand': forms.Select(attrs={
                'class': 'form-control'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'iva_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código de barras'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Largo x Ancho x Alto'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['brand'].queryset = Brand.objects.filter(is_active=True)

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if sku:
            sku = sku.strip().upper()
            qs = Product.objects.filter(sku=sku)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'Ya existe un producto con el SKU "{sku}".')
        return sku

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description or not description.strip():
            raise forms.ValidationError('La descripción del producto es obligatoria.')
        return description.strip()


class CategoryForm(forms.ModelForm):
    """Formulario para crear y editar categorías"""
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la categoría',
                'rows': 4
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if not name:
                raise forms.ValidationError('El nombre de la categoría es obligatorio.')
        return name


class BrandForm(forms.ModelForm):
    """Formulario para crear y editar marcas"""
    
    class Meta:
        model = Brand
        fields = ['name', 'description', 'logo', 'website', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la marca'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la marca',
                'rows': 4
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if not name:
                raise forms.ValidationError('El nombre de la marca es obligatorio.')
        return name


