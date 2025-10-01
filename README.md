# NaturalMede - Sistema de Tienda Naturista

Sistema completo de gestión para tienda naturista desarrollado en Django, inspirado en [NaturalMede](https://www.instagram.com/naturalmede/).

## 🚀 Características

### Catálogo de Productos
- ✅ Gestión de categorías, marcas y productos
- ✅ Imágenes múltiples por producto
- ✅ Precios con IVA configurable
- ✅ Códigos de barras y SKU
- ✅ Productos destacados
- ✅ Búsqueda avanzada y filtros

### Carrito de Compras
- ✅ Carrito de sesión y usuario
- ✅ Gestión de cantidades
- ✅ Cálculo automático de totales e IVA
- ✅ Integración con WhatsApp

### Checkout y Órdenes
- ✅ Múltiples métodos de pago:
  - Contraentrega
  - Transferencia Bancolombia
  - Addi (stub)
- ✅ Estados de orden: nuevo, pendiente, pagado, enviado, entregado, cancelado
- ✅ Cálculo de costos de envío por ciudad/peso

### Inventario
- ✅ Control de stock por bodegas
- ✅ Transferencias internas entre bodegas
- ✅ Movimientos de stock automáticos
- ✅ Alertas de stock bajo
- ✅ Múltiples bodegas con bodega principal

### POS (Punto de Venta)
- ✅ Sesiones de caja
- ✅ Lector de código de barras
- ✅ Ventas rápidas
- ✅ Múltiples métodos de pago
- ✅ Control de efectivo

### Gestión de Clientes
- ✅ Clientes normales y VIP
- ✅ Múltiples direcciones por cliente
- ✅ Historial de compras
- ✅ Información de contacto completa

### Reportes y Dashboard
- ✅ Reportes de ventas
- ✅ Reportes de inventario
- ✅ Reportes de productos más vendidos
- ✅ Reportes financieros
- ✅ Exportación a CSV
- ✅ Dashboard con estadísticas

### API REST
- ✅ API completa con Django REST Framework
- ✅ Endpoints para catálogo, carrito y órdenes
- ✅ Autenticación y permisos
- ✅ Documentación automática

### Frontend
- ✅ Bootstrap 4.5.2 responsive
- ✅ Diseño moderno y limpio
- ✅ Integración con WhatsApp
- ✅ Interfaz intuitiva

## 🛠️ Instalación

### Requisitos
- Python 3.8+
- Django 4.2+
- SQLite (incluido con Python)

### 🗄️ Base de Datos SQLite

Este proyecto usa **SQLite** como base de datos por defecto, lo que significa:

- ✅ **Sin instalación adicional** - SQLite viene incluido con Python
- ✅ **Archivo único** - Toda la base de datos en `db.sqlite3`
- ✅ **Portable** - Puedes mover el proyecto completo copiando la carpeta
- ✅ **Perfecto para desarrollo** - Ideal para pruebas y desarrollo
- ✅ **Backup simple** - Solo copia el archivo `db.sqlite3`

### Pasos de Instalación

1. **Instalar dependencias**
```bash
pip install Django==4.2.7
pip install djangorestframework==3.14.0
pip install Pillow==10.1.0
pip install django-cors-headers==4.3.1
```

2. **Aplicar migraciones del sistema Django**
```bash
python manage.py migrate
```

3. **Crear migraciones de las aplicaciones**
```bash
python manage.py makemigrations
```

4. **Aplicar migraciones de las aplicaciones**
```bash
python manage.py migrate
```

5. **Importar datos de ejemplo**
```bash
python manage.py import_demo_data
```

6. **Crear superusuario**
```bash
python manage.py createsuperuser
```

7. **Ejecutar servidor**
```bash
python manage.py runserver
```

### Solución de Problemas

Si encuentras el error "no such table: catalog_product":

```bash
python manage.py makemigrations
python manage.py migrate
```

Si hay migraciones pendientes:

```bash
python manage.py migrate
python manage.py makemigrations
python manage.py migrate
```

8. **Acceder a la aplicación**
- Frontend: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- API: http://127.0.0.1:8000/api/

## 📊 Datos de Ejemplo

El comando `import_demo_data` crea:

### Usuarios
- **admin/admin123** - Superusuario
- **cliente_ejemplo/cliente123** - Cliente de prueba

### Categorías
- Suplementos
- Productos Orgánicos
- Cuidado Personal
- Tés e Infusiones
- Aromaterapia
- Medicina Natural

### Marcas
- Nature's Way
- Organic Valley
- Weleda
- Twinings
- Young Living
- Boiron

### Productos
- 12 productos de ejemplo con precios, descripciones y stock
- Imágenes placeholder
- Códigos de barras únicos
- Stock en 2 bodegas

### Bodegas
- Bodega Principal (Bogotá)
- Bodega Medellín

### Tarifas de Envío
- Configuradas para Bogotá, Medellín, Cali y Barranquilla
- Por rangos de peso (0-1kg, 1-3kg, 3-5kg)

## 🔧 Configuración

### Variables de Entorno

```env
SECRET_KEY=tu-secret-key-django
DEBUG=True
WHATSAPP_PHONE=+573001234567
```

### Base de Datos

El proyecto usa **SQLite** por defecto, que es perfecto para desarrollo y pequeñas aplicaciones. El archivo de base de datos se crea automáticamente como `db.sqlite3` en el directorio del proyecto.

**Ventajas de SQLite:**
- ✅ No requiere instalación adicional
- ✅ Archivo único y portable
- ✅ Perfecto para desarrollo
- ✅ Ideal para aplicaciones pequeñas y medianas
- ✅ Backup simple (copiar el archivo)

**Para producción con mayor volumen**, puedes cambiar a PostgreSQL editando `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'naturalmede',
        'USER': 'usuario',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📱 Uso

### Frontend Público
1. **Catálogo**: Navegar por productos, categorías y marcas
2. **Carrito**: Agregar productos, modificar cantidades
3. **Checkout**: Completar información y seleccionar método de pago
4. **WhatsApp**: Pedir productos directamente por WhatsApp

### Panel Administrativo
1. **Productos**: Gestionar catálogo, categorías, marcas
2. **Inventario**: Control de stock, transferencias, movimientos
3. **Órdenes**: Procesar pedidos, actualizar estados
4. **Clientes**: Gestionar información de clientes
5. **POS**: Punto de venta en tienda
6. **Reportes**: Análisis de ventas, inventario y finanzas

### API REST
- **GET /api/products/** - Listar productos
- **POST /api/cart/add/** - Agregar al carrito
- **GET /api/orders/** - Listar órdenes
- **POST /api/orders/{id}/status/** - Actualizar estado

## 🚀 Despliegue

### Heroku
1. Crear `Procfile`:
```
web: gunicorn naturalmede.wsgi --log-file -
```

2. Configurar variables de entorno en Heroku
3. Desplegar con Git

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "naturalmede.wsgi"]
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o consultas:
- Email: soporte@naturalmede.com
- WhatsApp: +57 300 123 4567

## 🔄 Changelog

### v1.0.0
- ✅ Sistema completo de tienda naturista
- ✅ Catálogo con categorías y marcas
- ✅ Carrito de compras
- ✅ Checkout con múltiples métodos de pago
- ✅ Sistema de inventario
- ✅ POS para tienda física
- ✅ Gestión de clientes
- ✅ Reportes y dashboard
- ✅ API REST completa
- ✅ Frontend responsive con Bootstrap
- ✅ Integración con WhatsApp

