from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db import transaction
from .models import Customer
from .serializers import CustomerSerializer


class CustomerListAPIView(generics.ListAPIView):
    """API para obtener lista de clientes"""
    queryset = Customer.objects.filter(is_active=True).select_related('user')
    serializer_class = CustomerSerializer


class CustomerCreateAPIView(generics.CreateAPIView):
    """API para crear nuevos clientes"""
    serializer_class = CustomerSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Extraer datos del request
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        email = request.data.get('email', '').strip()
        phone = request.data.get('phone', '').strip()
        document = request.data.get('document', '').strip()
        
        # Validaciones básicas
        if not first_name or not last_name:
            return Response(
                {'error': 'Nombre y apellido son obligatorios'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Crear username único
            username = email if email else f"{first_name.lower()}.{last_name.lower()}"
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email if email else '',
                password=User.objects.make_random_password()  # Password aleatorio
            )
            
            # Generar número de documento único si no se proporciona
            if not document:
                document = f"CC{user.id:06d}"
            
            # Asegurar que el documento sea único
            counter = 1
            original_document = document
            while Customer.objects.filter(document_number=document).exists():
                document = f"{original_document}{counter}"
                counter += 1
            
            # Crear cliente con campos requeridos
            customer = Customer.objects.create(
                user=user,
                customer_type='normal',
                document_type='CC',  # Por defecto Cédula de Ciudadanía
                document_number=document,
                phone=phone if phone else '0000000000',  # Teléfono por defecto
                address='Dirección no especificada',  # Dirección por defecto
                city='Ciudad no especificada',  # Ciudad por defecto
                is_active=True
            )
            
            serializer = self.get_serializer(customer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Error al crear cliente: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
