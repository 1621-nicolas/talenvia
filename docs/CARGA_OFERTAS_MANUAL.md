# Registrar ofertas laborales manualmente en Talenvía

En Talenvía, las **ofertas laborales** son las publicaciones que aparecen en **Empleos**. Las **postulaciones** se generan después, cuando una persona postulante envía su CV y consentimiento. Son dos registros distintos.

## Opción A — Cuatro ofertas ficticias inmediatas

Solo en desarrollo local:

```powershell
git pull origin main
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py sembrar_demo --confirmar
.\.venv\Scripts\python.exe manage.py runserver
```

El comando crea (sin duplicarlas al ejecutarlo otra vez) cuatro empresas y ofertas **DEMO ficticias** en Trujillo, Lima, Arequipa y Piura; son pruebas, no vacantes reales. Se bloquea en producción (`DJANGO_DEBUG=false`).

La base de datos usada por defecto es `db.sqlite3`, en la raíz del proyecto. No subas esa base con datos personales a GitHub.

## Opción B — Agregar ofertas individualmente desde Django Admin

1. Arranca el servidor; inicia sesión como administrador en `http://127.0.0.1:8000/administracion/`. Si no existe, crea el usuario con `python manage.py createsuperuser`.
2. En el catálogo **Apoyos**, agrega los apoyos que la empresa realmente ofrecería (por ejemplo, acceso sin escalones, comunicación escrita).
3. Registra una empresa desde la web con el rol Empresa, completa su perfil y RUC, y en el administrador busca **Empresas**, selecciona la que corresponde y ejecuta **Aprobar empresas con datos completos**.
4. En el administrador, abre **Ofertas laborales → Añadir**. Selecciona la empresa aprobada, escribe título, descripción y requisitos, ubicación en Perú, modalidad, fecha de cierre futura y los apoyos ofrecidos. Selecciona `PUBLICADA` y pulsa **Guardar**.
5. Visita `http://127.0.0.1:8000/ofertas/` para comprobar que la oferta esté visible. Debe pertenecer a una empresa aprobada, activa y con perfil completo; también debe estar publicada y no haber vencido.

Las empresas pendientes, suspendidas o sin datos completos no pueden publicar ofertas. Las ofertas cerradas no aparecen en resultados. Para evitar cambiar las condiciones ofrecidas a postulantes, las ofertas que ya recibieron postulaciones no pueden editarse.

## Importante para el proyecto ODS 10

- Describe las **condiciones de apoyo del puesto**, no el tipo de discapacidad de los postulantes.
- No se exige diagnóstico ni certificado.
- No inventes empleos reales ni uses logos de empresas sin autorización.
- Si son ejemplos, coloca `DEMO` en nombre y descripción para distinguirlos.
- No uses estas ofertas como evidencia de contrataciones o impacto real para el paper.
