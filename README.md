# Motos Boris

Aplicación web sencilla para consultar y cargar precios de servicios de motos.

## Ejecutar en local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:5000`. La base de datos `motos_boris.sqlite3` se crea automáticamente.

La carga de precios está protegida en `/admin`. Configura las credenciales y la clave de sesión en un archivo `.env` local antes de iniciar:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=una-clave-larga-y-unica
SECRET_KEY=otra-clave-secreta-larga-y-unica
```

El archivo `.env` está excluido de Git. No publiques sus valores ni uses contraseñas por defecto.

Los precios se guardan en pesos argentinos como números enteros. Para activar WhatsApp, define `WHATSAPP_NUMBER` en `static/app.js` con el número internacional sin `+` ni espacios.

Desde el panel privado también puedes editar o borrar cada presupuesto y aplicar un aumento porcentual a todo el catálogo.

## Publicar en PythonAnywhere

1. Sube el proyecto y crea un entorno virtual desde una consola Bash:
	`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
2. En **Web**, crea una aplicación Flask y configura el archivo WSGI para importar:
	`from app import app as application`
3. Define el directorio de trabajo del WSGI como la carpeta del proyecto y selecciona `.venv` como entorno virtual.
4. Recarga la aplicación. La SQLite se generará en el directorio del proyecto al primer arranque.

En PythonAnywhere configura `ADMIN_USERNAME`, `ADMIN_PASSWORD` y `SECRET_KEY` desde **Web > Environment variables**, guarda y pulsa **Reload**. Las variables del entorno tienen prioridad y no deben escribirse en el repositorio.
