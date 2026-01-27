# Instrucciones para Debug de Creación de Compras

## 🔍 Estado Actual

### ✅ Problemas Resueltos:
1. **Prefijo del formset**: Corregido de `formset-__prefix__` a `items-__prefix__`
2. **Configuración del formset**: `min_num=0` y `validate_min=False`
3. **Logo.png**: Creado archivo temporal para eliminar error 404
4. **Debugging agregado**: Logs en la vista para ver datos recibidos

### 🔧 Debugging Implementado:
- **Logs de datos POST**: Muestra qué datos llegan al servidor
- **Validación de formularios**: Muestra si cada formulario es válido
- **Conteo de items**: Muestra cuántos productos válidos se encontraron

## 🚀 Instrucciones para Probar

### 1. Acceder al Formulario
```
http://127.0.0.1:8000/purchases/purchases/create/
```

### 2. Completar el Formulario
1. **Seleccionar proveedor**: Elegir "MOLI" o "Pepito Perez Sas"
2. **Fecha de orden**: Usar fecha actual
3. **Estado**: Dejar "Pendiente"
4. **Estado de pago**: Dejar "Pendiente"
5. **Costo de envío**: Dejar 0.00

### 3. Agregar Productos
1. **Hacer clic en "Agregar Producto"**
2. **Buscar producto**: Escribir "COLAGENO" o "Echinacea"
3. **Seleccionar producto**: Hacer clic en la sugerencia
4. **Completar campos**:
   - Cantidad: 10
   - Costo unitario: 100.00
   - IVA %: 19.00
   - Desc. %: 0.00

### 4. Enviar Formulario
1. **Hacer clic en "Crear Compra"**
2. **Revisar logs en terminal**: Deberían aparecer los datos de debug

## 📋 Qué Esperar

### ✅ Si Funciona Correctamente:
```
=== DEBUG PURCHASE CREATE ===
POST data keys: ['supplier', 'order_date', 'status', 'payment_status', 'shipping_cost', 'notes', 'items-TOTAL_FORMS', 'items-INITIAL_FORMS', 'items-MIN_NUM_FORMS', 'items-MAX_NUM_FORMS', 'items-0-product', 'items-0-quantity', 'items-0-unit_cost', 'items-0-tax_percentage', 'items-0-discount_percentage']
Formset data: {'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '0', 'items-MIN_NUM_FORMS': '0', 'items-MAX_NUM_FORMS': '1000', 'items-0-product': '14', 'items-0-quantity': '10', 'items-0-unit_cost': '100.00', 'items-0-tax_percentage': '19.00', 'items-0-discount_percentage': '0.00'}
=============================
Formulario principal válido: True
Formset válido: True
Items válidos encontrados: 1
```

### ❌ Si Hay Problemas:
- **Datos faltantes**: Verificar que el JavaScript esté enviando todos los campos
- **Formulario inválido**: Revisar errores específicos
- **Items inválidos**: Verificar que los productos se estén agregando correctamente

## 🎯 Próximos Pasos

1. **Probar en el navegador** siguiendo las instrucciones
2. **Revisar logs** en el terminal del servidor Django
3. **Reportar resultados** para identificar el problema específico
4. **Ajustar solución** según los datos de debug obtenidos

## 🔧 Archivos Modificados

- `purchases/views.py`: Agregado debugging
- `purchases/templates/purchases/purchase_form.html`: Corregido prefijo
- `purchases/forms.py`: Configuración del formset mejorada
- `static/images/logo.png`: Creado archivo temporal

¡Listo para probar y obtener datos de debug específicos!


