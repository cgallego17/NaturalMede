from django import forms
from django.contrib.auth.models import User
from .models import Customer, CustomerAddress


class CustomerForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Dejar vacío para mantener la contraseña actual'
    )

    class Meta:
        model = Customer
        fields = [
            'customer_type', 'document_type', 'document_number', 'phone',
            'address', 'city', 'birth_date', 'notes', 'is_active'
        ]
        widgets = {
            'customer_type': forms.Select(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def clean_document_number(self):
        document_number = self.cleaned_data.get('document_number')
        if document_number:
            document_number = document_number.strip()
            qs = Customer.objects.filter(document_number=document_number)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'Ya existe un cliente con el documento "{document_number}".')
        return document_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
            qs = User.objects.filter(email=email)
            if self.instance and self.instance.user:
                qs = qs.exclude(pk=self.instance.user.pk)
            if qs.exists():
                raise forms.ValidationError(f'Ya existe un usuario con el email "{email}".')
        return email

    def save(self, commit=True):
        customer = super().save(commit=False)
        
        if customer.user:
            # Actualizar usuario existente
            customer.user.first_name = self.cleaned_data['first_name']
            customer.user.last_name = self.cleaned_data['last_name']
            customer.user.email = self.cleaned_data['email']
            
            password = self.cleaned_data.get('password')
            if password:
                customer.user.set_password(password)
            
            customer.user.save()
        else:
            # Crear nuevo usuario
            user = User.objects.create_user(
                username=self.cleaned_data['email'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=self.cleaned_data.get('password', 'defaultpassword123')
            )
            customer.user = user
        
        if commit:
            customer.save()
        
        return customer


class CustomerAddressForm(forms.ModelForm):
    class Meta:
        model = CustomerAddress
        fields = ['name', 'address', 'city', 'phone', 'notes', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }













