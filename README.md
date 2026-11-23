# Gestor de Inventario

Trabajo Práctico Integrador de Análisis y Metodologías de Sistemas (Da Vinci).

Sistema web para llevar el inventario de un comercio: productos, categorías y proveedores, con un dashboard de métricas. Está hecho en Python con Flask, plantillas Jinja2 y Flask-SQLAlchemy sobre SQLite.

## Módulos

- **Login:** registro, inicio y cierre de sesión. Sin sesión no se puede entrar al resto del sistema.
- **Dashboard:** métricas del inventario, valor por categoría, proveedores y productos con stock bajo.
- **Inventario:** alta, listado, búsqueda, modificación y baja de productos y categorías.
- **Proveedores:** alta, listado, modificación y baja de proveedores.

## Cómo ejecutarlo

1. Clonar el repositorio y entrar a la carpeta.
2. Crear y activar el entorno virtual:

```
python -m venv env
.\env\Scripts\activate
```

3. Instalar las dependencias:

```
pip install -r requirements.txt
```

4. Crear un archivo `.env` en la raíz con:

```
SECRET_KEY=una-clave-larga-y-secreta
DATABASE_URL=sqlite:///inventario.db
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret
```

Las credenciales de Google se crean en Google Cloud Console (Credenciales > ID de cliente de OAuth > Aplicación web). En "URI de redireccionamiento autorizados" hay que cargar `http://127.0.0.1:5000/auth/google/callback` y, en Render, `https://TU-APP.onrender.com/auth/google/callback`. Si las variables no están definidas, el botón "Continuar con Google" no se muestra y el login con email y contraseña sigue funcionando.

5. Levantar la aplicación:

```
python run.py
```

6. Abrir http://127.0.0.1:5000 en el navegador y crear una cuenta desde "Registrate".

La base de datos se crea sola la primera vez, dentro de la carpeta `instance/`.

## Tests

Se ejecutan con:

```
pytest
```

Por ahora incluye los tests del login (`tests/test_auth.py`):

- la contraseña se guarda hasheada y no en texto plano
- no se puede registrar dos veces el mismo email
- una ruta protegida sin sesión redirige al login
- se puede iniciar y cerrar sesión
- una contraseña incorrecta muestra el mensaje de error

## Estructura

```
run.py                 punto de entrada: levanta la aplicación
app/
  __init__.py          create_app() y registro de blueprints
  config.py            configuración leída desde .env
  extensions.py        base de datos, bcrypt y login
  models.py            User, Category, Supplier y Product
  blueprints/
    auth.py            login
    dashboard.py       dashboard
    inventory.py       productos y categorías
    supplier.py        proveedores
  templates/           plantillas HTML
  static/css/          estilos (styles.css)
mcp_inventario/        servidor MCP del gestor
seeds/                 datos de prueba
tests/                 tests con pytest
```

## Equipo

- Integrante 1: base del proyecto y login
- Integrante 2: inventario
- Integrante 3: proveedores y dashboard
