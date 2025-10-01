# Sistema de Auditoría - NaturalMede

## Descripción

El sistema de auditoría de NaturalMede proporciona un registro completo y detallado de todas las actividades importantes que ocurren en el sistema. Permite rastrear cambios en datos, acciones de usuarios, eventos de seguridad y actividad del sistema.

## Características Principales

### 🔍 **Rastreo Automático**
- **Creación, actualización y eliminación** de objetos
- **Inicio y cierre de sesión** de usuarios
- **Cambios de estado** en órdenes, ventas, inventario
- **Transferencias de stock** y movimientos de inventario
- **Eventos críticos** del sistema

### 📊 **Dashboard Interactivo**
- **Estadísticas en tiempo real** de actividad
- **Gráficos de actividad diaria** y por tipo de acción
- **Eventos críticos y fallidos** destacados
- **Actividad por usuario** en los últimos 30 días

### 🔎 **Búsqueda y Filtrado Avanzado**
- **Filtros por usuario, acción, severidad y fecha**
- **Búsqueda de texto** en mensajes y objetos
- **Paginación** para manejar grandes volúmenes de datos
- **Exportación a CSV** de resultados filtrados

### 📋 **Reportes Personalizados**
- **Generación de reportes** por tipo de evento
- **Filtros personalizables** por fecha, usuario, acción
- **Exportación automática** a formato CSV
- **Seguimiento del estado** de generación

## Modelos Principales

### `AuditLog`
Registro principal de auditoría que contiene:
- **Usuario** que realizó la acción
- **Tipo de acción** (CREATE, UPDATE, DELETE, LOGIN, etc.)
- **Objeto afectado** (con referencia genérica)
- **Valores anteriores y nuevos** (para cambios)
- **Severidad** (LOW, MEDIUM, HIGH, CRITICAL)
- **Estado** (SUCCESS, FAILED, PENDING, CANCELLED)
- **Contexto** (IP, User Agent, Sesión)
- **Metadatos** adicionales

### `AuditConfiguration`
Configuración de auditoría por modelo:
- **Habilitar/deshabilitar** auditoría por modelo
- **Campos específicos** a rastrear
- **Tipos de eventos** a capturar
- **Nivel de severidad** por defecto
- **Días de retención** de logs

### `AuditReport`
Reportes generados:
- **Tipo de reporte** y parámetros utilizados
- **Estado de generación** y archivo resultante
- **Metadatos** del reporte (tamaño, duración)

## Configuración

### 1. Configuración Automática
```bash
# Configurar auditoría para modelos importantes
python manage.py setup_audit

# Habilitar auditoría para todos los modelos
python manage.py setup_audit --enable-all

# Deshabilitar auditoría para todos los modelos
python manage.py setup_audit --disable-all
```

### 2. Configuración Manual
```python
from audit.models import AuditConfiguration
from django.contrib.contenttypes.models import ContentType

# Configurar auditoría para un modelo específico
content_type = ContentType.objects.get_for_model(Product)
config = AuditConfiguration.objects.create(
    content_type=content_type,
    is_enabled=True,
    track_creates=True,
    track_updates=True,
    track_deletes=True,
    severity_level='MEDIUM',
    retention_days=365
)
```

## Uso Programático

### Crear Logs Manuales
```python
from audit.signals import create_audit_log

# Crear log de auditoría manual
create_audit_log(
    user=request.user,
    action='CUSTOM_ACTION',
    obj=product,
    message='Producto modificado manualmente',
    severity='HIGH',
    old_values={'price': 100},
    new_values={'price': 120},
    request=request
)
```

### Verificar Configuración
```python
from audit.utils import is_audit_enabled_for_model, get_audit_stats

# Verificar si auditoría está habilitada
if is_audit_enabled_for_model(Product):
    print("Auditoría habilitada para Product")

# Obtener estadísticas
stats = get_audit_stats()
print(f"Total de logs: {stats['total_logs']}")
```

## Comandos de Gestión

### Limpieza de Logs Antiguos
```bash
# Limpiar logs según configuración de retención
python manage.py cleanup_audit_logs

# Simular limpieza sin eliminar
python manage.py cleanup_audit_logs --dry-run

# Limpiar logs anteriores a 30 días
python manage.py cleanup_audit_logs --days 30
```

### Datos de Demostración
```bash
# Crear 100 logs de demostración
python manage.py create_audit_demo_data --count 100

# Crear logs de los últimos 7 días
python manage.py create_audit_demo_data --days 7
```

## URLs y Vistas

### URLs Principales
- `/audit/` - Dashboard de auditoría
- `/audit/logs/` - Lista de logs con filtros
- `/audit/logs/<id>/` - Detalle de log específico
- `/audit/export/` - Exportar logs a CSV
- `/audit/reports/generate/` - Generar reportes
- `/audit/api/` - API para gráficos y datos

### Permisos Requeridos
- `audit.view_auditlog` - Ver logs de auditoría
- `audit.add_auditreport` - Generar reportes
- `audit.change_auditconfiguration` - Configurar auditoría

## Tipos de Acciones Rastreadas

### Acciones de Datos
- `CREATE` - Creación de objetos
- `UPDATE` - Actualización de objetos
- `DELETE` - Eliminación de objetos
- `VIEW` - Visualización de objetos

### Acciones de Usuario
- `LOGIN` - Inicio de sesión
- `LOGOUT` - Cierre de sesión
- `PASSWORD_CHANGE` - Cambio de contraseña
- `PROFILE_UPDATE` - Actualización de perfil

### Acciones de Sistema
- `EXPORT` - Exportación de datos
- `IMPORT` - Importación de datos
- `PRINT` - Impresión de documentos
- `EMAIL` - Envío de emails
- `BACKUP` - Respaldo del sistema
- `RESTORE` - Restauración del sistema

### Acciones de Negocio
- `CANCEL` - Cancelación de órdenes
- `APPROVE` - Aprobación de procesos
- `REJECT` - Rechazo de procesos
- `COMPLETE` - Completar procesos
- `TRANSFER` - Transferencias de stock
- `RECEIVE` - Recepción de productos
- `RETURN` - Devoluciones
- `REFUND` - Reembolsos
- `DISCOUNT` - Aplicación de descuentos
- `PAYMENT` - Procesamiento de pagos

## Niveles de Severidad

- **LOW** - Actividades rutinarias (login, logout, visualizaciones)
- **MEDIUM** - Cambios normales de datos (crear, actualizar productos)
- **HIGH** - Cambios importantes (transferencias, cancelaciones)
- **CRITICAL** - Eventos críticos (errores de sistema, accesos no autorizados)

## Estados de Logs

- **SUCCESS** - Acción completada exitosamente
- **FAILED** - Acción falló o tuvo error
- **PENDING** - Acción en progreso
- **CANCELLED** - Acción cancelada

## Integración con Django Admin

El sistema de auditoría se integra completamente con el Django Admin:

- **Vista de logs** con filtros y búsqueda avanzada
- **Configuración de auditoría** por modelo
- **Gestión de reportes** generados
- **Estadísticas** y resúmenes

## Consideraciones de Rendimiento

### Optimizaciones Implementadas
- **Índices de base de datos** en campos frecuentemente consultados
- **Paginación** para evitar cargar todos los logs
- **Consultas optimizadas** con select_related y prefetch_related
- **Limpieza automática** de logs antiguos

### Recomendaciones
- **Configurar retención** apropiada según necesidades
- **Monitorear tamaño** de la base de datos
- **Usar filtros** para consultas específicas
- **Generar reportes** en horarios de bajo tráfico

## Seguridad

### Datos Sensibles
- **No se registran contraseñas** ni datos sensibles
- **IP y User Agent** se registran para trazabilidad
- **Sesiones** se vinculan a logs de usuario
- **Permisos** controlan acceso a logs

### Cumplimiento
- **Registro completo** de actividades para auditorías
- **Retención configurable** según políticas
- **Exportación** para análisis externos
- **Trazabilidad** completa de cambios

## Troubleshooting

### Problemas Comunes

1. **Logs no se generan**
   - Verificar que `AuditConfiguration` esté habilitada
   - Confirmar que las señales estén registradas
   - Revisar permisos de usuario

2. **Rendimiento lento**
   - Verificar índices de base de datos
   - Limpiar logs antiguos
   - Usar filtros en consultas

3. **Espacio en disco**
   - Configurar retención apropiada
   - Ejecutar limpieza regular
   - Monitorear crecimiento

### Logs de Debug
```python
# Habilitar logs de debug
import logging
logging.getLogger('audit').setLevel(logging.DEBUG)
```

## Contribución

Para contribuir al sistema de auditoría:

1. **Mantener compatibilidad** con modelos existentes
2. **Agregar tests** para nuevas funcionalidades
3. **Documentar cambios** en configuración
4. **Considerar rendimiento** en implementaciones

## Licencia

Este sistema de auditoría es parte del proyecto NaturalMede y sigue la misma licencia del proyecto principal.
