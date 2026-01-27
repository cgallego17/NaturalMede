#!/usr/bin/env python
"""
Script para probar que todas las importaciones funcionen correctamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naturalmede.settings')
django.setup()

def test_imports():
    """Probar todas las importaciones del proyecto"""
    try:
        print("Probando importaciones...")
        
        # Probar importaciones de modelos
        from catalog.models import Category, Brand, Product, Cart, CartItem
        print("✓ Modelos de catálogo importados correctamente")
        
        from inventory.models import Warehouse, Stock, StockMovement, StockTransfer
        print("✓ Modelos de inventario importados correctamente")
        
        from customers.models import Customer, CustomerAddress
        print("✓ Modelos de clientes importados correctamente")
        
        from orders.models import Order, OrderItem, ShippingRate
        print("✓ Modelos de órdenes importados correctamente")
        
        from pos.models import POSSession, POSSale, POSSaleItem
        print("✓ Modelos de POS importados correctamente")
        
        from reports.models import ReportTemplate, ReportSchedule
        print("✓ Modelos de reportes importados correctamente")
        
        # Probar importaciones de vistas
        from catalog.views import ProductListView, ProductDetailView, CartView
        print("✓ Vistas de catálogo importadas correctamente")
        
        from inventory.views import InventoryDashboardView, StockListView
        print("✓ Vistas de inventario importadas correctamente")
        
        from customers.views import CustomerListView, CustomerDetailView
        print("✓ Vistas de clientes importadas correctamente")
        
        from orders.views import OrderListView, OrderDetailView
        print("✓ Vistas de órdenes importadas correctamente")
        
        from pos.views import POSDashboardView, POSSaleView
        print("✓ Vistas de POS importadas correctamente")
        
        from reports.views import ReportsDashboardView, SalesReportView
        print("✓ Vistas de reportes importadas correctamente")
        
        # Probar importaciones de formularios
        from catalog.forms import CartAddForm, CheckoutForm
        print("✓ Formularios de catálogo importados correctamente")
        
        from inventory.forms import StockMovementForm, StockTransferForm
        print("✓ Formularios de inventario importados correctamente")
        
        from customers.forms import CustomerForm, CustomerAddressForm
        print("✓ Formularios de clientes importados correctamente")
        
        from orders.forms import OrderForm, ShippingRateForm
        print("✓ Formularios de órdenes importados correctamente")
        
        from pos.forms import POSSaleForm, POSSaleItemForm
        print("✓ Formularios de POS importados correctamente")
        
        # Probar importaciones de serializers
        from catalog.serializers import ProductSerializer, CategorySerializer
        print("✓ Serializers de catálogo importados correctamente")
        
        from orders.serializers import OrderSerializer, OrderItemSerializer
        print("✓ Serializers de órdenes importados correctamente")
        
        from customers.serializers import CustomerSerializer, CustomerAddressSerializer
        print("✓ Serializers de clientes importados correctamente")
        
        print("\n🎉 ¡Todas las importaciones funcionan correctamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error en importaciones: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)












