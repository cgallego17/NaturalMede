# GitHub Actions para NaturalMede

Este directorio contiene las configuraciones de GitHub Actions para automatizar las pruebas y el despliegue del proyecto NaturalMede.

## Workflows Disponibles

### 1. CI/CD Pipeline (`ci.yml`)

**Trigger:** Push a `main` o `develop`, Pull Requests

**Jobs:**
- **test**: Ejecuta las pruebas unitarias con pytest
- **quality**: Verifica la calidad del código (formato, linting, seguridad)
- **build**: Construye la aplicación y verifica que esté lista para producción

**Características:**
- ✅ Pruebas con PostgreSQL
- ✅ Cobertura de código con Codecov
- ✅ Formateo de código con Black
- ✅ Linting con flake8
- ✅ Análisis de seguridad con Bandit
- ✅ Verificación de dependencias con Safety
- ✅ Verificación de sistema Django

### 2. Deploy to Production (`deploy.yml`)

**Trigger:** Push a `main`, Manual dispatch

**Jobs:**
- **deploy**: Despliega la aplicación a producción

**Características:**
- ✅ Ejecuta pruebas antes del despliegue
- ✅ Recolecta archivos estáticos
- ✅ Ejecuta migraciones de base de datos
- ✅ Despliegue automatizado

## Configuración Requerida

### Secrets de GitHub

Para que los workflows funcionen correctamente, necesitas configurar los siguientes secrets en tu repositorio:

1. **SECRET_KEY**: Clave secreta de Django
2. **DATABASE_URL**: URL de conexión a la base de datos de producción
3. **DEPLOY_KEY**: Clave SSH para el despliegue
4. **SERVER_HOST**: Host del servidor de producción

### Configuración de Codecov

1. Ve a [codecov.io](https://codecov.io)
2. Conecta tu repositorio de GitHub
3. Obtén el token de Codecov
4. Agrega el token como secret `CODECOV_TOKEN` en GitHub

## Uso

### Ejecutar Pruebas Localmente

```bash
# Instalar dependencias de prueba
pip install pytest pytest-django pytest-cov black flake8 bandit safety

# Ejecutar pruebas
pytest --cov=. -v

# Verificar formato de código
black --check .

# Verificar linting
flake8 .

# Verificar seguridad
bandit -r .

# Verificar dependencias
safety check
```

### Verificar Workflows

1. Ve a la pestaña "Actions" en tu repositorio de GitHub
2. Selecciona el workflow que quieres ejecutar
3. Haz clic en "Run workflow"

## Estructura de Archivos

```
.github/
├── workflows/
│   ├── ci.yml          # Pipeline principal de CI/CD
│   └── deploy.yml      # Despliegue a producción
└── README.md           # Este archivo
```

## Personalización

### Agregar Nuevas Pruebas

1. Crea archivos de prueba en el directorio `tests/`
2. Las pruebas se ejecutarán automáticamente en el workflow `ci.yml`

### Modificar el Despliegue

1. Edita el archivo `deploy.yml`
2. Agrega tus comandos de despliegue en la sección "Deploy to server"

### Agregar Nuevos Checks de Calidad

1. Edita el archivo `ci.yml`
2. Agrega nuevos pasos en el job `quality`

## Troubleshooting

### Errores Comunes

1. **Tests fallan**: Verifica que todas las dependencias estén en `requirements.txt`
2. **Build falla**: Verifica que no haya errores de sintaxis en el código
3. **Deploy falla**: Verifica que los secrets estén configurados correctamente

### Logs

Los logs de cada workflow están disponibles en la pestaña "Actions" de GitHub.

## Contribución

Para contribuir a los workflows:

1. Haz un fork del repositorio
2. Crea una rama para tu feature
3. Modifica los archivos de workflow
4. Haz un pull request

## Recursos Adicionales

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [flake8 Documentation](https://flake8.pycqa.org/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/)
