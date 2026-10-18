# Registro empresarial e interacción accesible — Entrega T2

## Función implementada

El registro público en `/registro/` distingue entre Postulante y Empresa. El enlace
«Para empresas» y el botón «Soy una empresa» preseleccionan el rol empresarial.

Si se elige **Empresa**, son obligatorios:

- Correo electrónico de acceso (único).
- Razón social (máximo 180 caracteres).
- RUC (11 dígitos; único para empresas registradas).
- Ciudad o ubicación (máximo 160 caracteres).
- Correo de contacto empresarial.
- Contraseña y confirmación (Django, mínimo 12 caracteres).

El alta de la cuenta y del perfil empresarial es **atómica**: errores impiden
crear una cuenta incompleta. El estado inicial es **PENDIENTE** y se requiere
aprobación administrativa antes de publicar o revisar candidatos.

> **Al iniciar sesión nuevamente no se piden estos datos**. Iniciar sesión
> continúa utilizando solamente correo y contraseña. Los datos empresariales
> se pueden revisar en el panel.

Para **Postulante** no se solicitan los datos de empresa; tampoco se exigen
diagnósticos médicos, certificados ni detalles sobre discapacidad.

## Mejoras de interfaz

- «Volver» visible y navegable por teclado en las páginas internas.
- Botones para mostrar/ocultar contraseña con estado accesible.
- Campos empresariales condicionales al seleccionar rol.
- Formularios que se pueden enviar con JS deshabilitado; Django valida siempre.
- Diseño turquesa/menta coherente con la identidad Talenvía ODS 10.

## Pruebas para T2 (semana 9)

- Tests `empleo.tests_registro_t2` validan alta, RUC incorrecto/repetido,
  campos obligatorios, aislamiento de rol y navegación.
- Prueba funcional con Playwright de alta empresarial y botones de contraseña
  en un entorno de pruebas aislado.
- Sin cambios de esquema ni migración SQL: se reutilizan las tablas existentes.

## Validación SQL Server sin tocar TalenviaDB

En el equipo local usar una cuenta autorizada a **crear una base nueva de
prueba** y no reutilizar `TalenviaDB`. Django Test Runner crea la base de
ensayo (nombre habitual `test_TalenviaDB`), aplica migraciones, ejecuta las
pruebas y elimina la base al terminar. Si la base de prueba ya existiera,
**detenerse y revisar** antes de aceptar operaciones destructivas.

```powershell
git pull origin main
$env:DB_ENGINE="sqlserver"
.\.venv\Scripts\python.exe manage.py test empleo.tests_registro_t2 -v 2
```

Si no hay permisos de creación, revisar con SSMS y configurar un servidor o
base de pruebas independiente. **No usar `--keepdb` o `--noinput`
sin evaluar el estado de la base de pruebas.**

Nunca compartir usuarios reales, contraseñas, CV ni datos empresariales
confidenciales en los resultados académicos. Las ofertas DEMO son ficticias.
