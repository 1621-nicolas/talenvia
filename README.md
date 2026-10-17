# Talenvía — Portal de empleo inclusivo · ODS 10

Proyecto académico **Calidad y Pruebas de Software** (UPN, 2026-2). Talenvía conecta personas con discapacidad y empresas mediante ofertas laborales que informan sus condiciones de accesibilidad. Contribuye al **ODS 10: Reducción de las desigualdades**, metas 10.2 y 10.3.

**Estado: primera implementación del prototipo.** No se deben publicar CV ni datos personales reales en el repositorio. Las métricas y comprobaciones WCAG son objetivos hasta que se ejecuten y documenten.

## Funcionalidades de la primera versión

- Registro e inicio de sesión por correo; roles Postulante / Empresa / Administrador.
- Perfiles profesionales y empresariales; apoyos opcionales y privados.
- Aprobación administrativa de empresas y catálogo de apoyos.
- Ofertas con requisitos, modalidad, ubicación, fecha y apoyos declarados.
- Filtros de búsqueda, paginación de 10 ofertas.
- CV PDF privado, máximo 5 000 000 bytes, preservación de versiones.
- Postulación con consentimiento expreso y prevención de duplicados.
- Historial privado del postulante y candidatos visibles solo para la empresa destinataria.
- Primeras pruebas automatizadas Django y pipeline de GitHub Actions.

## Ejecutar en Windows PowerShell

Requiere Python 3.12+ (versión compatible con Django 5.2).

```powershell
git clone https://github.com/1621-nicolas/talenvia.git
cd talenvia
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py sembrar_apoyos
python manage.py createsuperuser
python manage.py runserver
```

Abrir **http://127.0.0.1:8000/**. El panel administrativo está en **http://127.0.0.1:8000/administracion/**.

> En el administrador, completa una empresa y usa la acción «Aprobar empresas con datos completos». El registro público no permite crear administradores.

Si PowerShell no permite activar entornos virtuales, ejecuta el intérprete directamente, por ejemplo: `.\.venv\Scripts\python.exe manage.py runserver`.

## Ejecutar las pruebas

```powershell
python manage.py check
python manage.py test empleo -v 2
coverage run --source=empleo manage.py test empleo
coverage report -m
python manage.py makemigrations --check --dry-run
```

## Seguridad y privacidad

- No se solicitan diagnósticos médicos ni certificados de discapacidad.
- Los CV se guardan en `private_uploads/`, excluido de Git, y se entregan únicamente por una vista que verifica permisos.
- Un administrador no obtiene acceso rutinario a los CV por su rol.
- Una empresa no puede descargar CV de postulaciones de otra empresa.
- El correo se normaliza, las contraseñas se protegen con hashing de Django y no existen contraseñas de demostración preestablecidas.
- El servidor de desarrollo es **solo local**. Antes de publicar en Internet, configurar una clave `DJANGO_SECRET_KEY` segura, `DJANGO_DEBUG=false`, dominios, HTTPS, cabeceras de seguridad y almacenamiento privado persistente.

## Documentación de calidad

Ver [Plan inicial de pruebas](docs/PLAN_PRUEBAS.md). El proyecto usa Django, HTML, CSS y SQLite según las prácticas de campo 01 y 02, con el diseño preparado para pruebas unitarias, funcionales, de rendimiento, seguridad y accesibilidad.

## Alcance del MVP

La selección laboral continúa fuera del portal por correo o teléfono. No incluye chat, entrevistas ni seguimiento de contratación. Las empresas declaran sus propios apoyos; la plataforma no certifica su accesibilidad.

## Diseño visual moderno e inclusivo (Diseño 1)

La interfaz adopta la propuesta **Moderno e Inclusivo**: turquesa, menta, blanco y azul oscuro; hero ilustrado, buscador de empleos, tarjetas con apoyos, formularios consistentes y paneles adaptables. La ilustración SVG original se guarda en `static/img/equipo-inclusivo.svg` y no depende de imágenes externas.

Ver [Guía de identidad visual](docs/IDENTIDAD_VISUAL.md) para componentes, paleta, pautas de accesibilidad y validación pendiente.

### Ver cuatro ofertas ficticias en desarrollo local

Después de `migrate`, ejecuta:

```powershell
python manage.py sembrar_apoyos
python manage.py sembrar_demo --confirmar
python manage.py runserver
```

**Advertencia:** las ofertas y empresas **DEMO** son ficticias, con correos `.invalid` y no representan vacantes reales. La carga se bloquea si `DJANGO_DEBUG=false`. Las cuentas DEMO no tienen contraseña utilizable. No uses estos datos como evidencia de contratación o impacto social real.

### Validación del rediseño

```powershell
python manage.py test empleo -v 2
```

Las pruebas verifican algunas estructuras y flujos; no sustituyen una evaluación manual WCAG 2.2 con NVDA, zoom al 200 % y herramientas de contraste, ni constituyen certificación de conformidad.
