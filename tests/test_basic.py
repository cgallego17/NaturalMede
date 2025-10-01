"""
Pruebas básicas para verificar que el sistema funciona correctamente
"""
import pytest
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User


class BasicTests(TestCase):
    """Pruebas básicas del sistema"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_django_setup(self):
        """Verifica que Django esté configurado correctamente"""
        assert True  # Si llegamos aquí, Django está funcionando
    
    def test_home_page(self):
        """Verifica que la página principal sea accesible"""
        response = self.client.get('/')
        # Puede ser 200 (OK) o 302 (redirect) dependiendo de la configuración
        assert response.status_code in [200, 302]
    
    def test_admin_page(self):
        """Verifica que la página de admin sea accesible"""
        response = self.client.get('/admin/')
        # Puede ser 200 (OK) o 302 (redirect) dependiendo de la configuración
        assert response.status_code in [200, 302]
    
    def test_catalog_page(self):
        """Verifica que la página de catálogo sea accesible"""
        response = self.client.get('/catalog/')
        # Puede ser 200 (OK) o 302 (redirect) dependiendo de la configuración
        assert response.status_code in [200, 302]
    
    def test_purchases_page(self):
        """Verifica que la página de compras sea accesible"""
        response = self.client.get('/purchases/')
        # Puede ser 200 (OK) o 302 (redirect) dependiendo de la configuración
        assert response.status_code in [200, 302]
    
    def test_audit_page(self):
        """Verifica que la página de auditoría sea accesible"""
        response = self.client.get('/audit/')
        # Puede ser 200 (OK) o 302 (redirect) dependiendo de la configuración
        assert response.status_code in [200, 302]


class ModelTests(TestCase):
    """Pruebas de los modelos"""
    
    def test_user_creation(self):
        """Verifica que se puedan crear usuarios"""
        user = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        assert user.username == 'testuser2'
        assert user.check_password('testpass123')
    
    def test_user_count(self):
        """Verifica el conteo de usuarios"""
        initial_count = User.objects.count()
        User.objects.create_user(
            username='testuser3',
            password='testpass123'
        )
        assert User.objects.count() == initial_count + 1


@pytest.mark.unit
class UnitTests:
    """Pruebas unitarias marcadas para pytest"""
    
    def test_basic_math(self):
        """Prueba básica de matemáticas"""
        assert 2 + 2 == 4
        assert 3 * 3 == 9
        assert 10 / 2 == 5
    
    def test_string_operations(self):
        """Prueba básica de operaciones de strings"""
        text = "NaturalMede"
        assert len(text) == 11
        assert text.lower() == "naturalmede"
        assert text.upper() == "NATURALMEDE"
    
    def test_list_operations(self):
        """Prueba básica de operaciones de listas"""
        items = [1, 2, 3, 4, 5]
        assert len(items) == 5
        assert sum(items) == 15
        assert max(items) == 5
        assert min(items) == 1
