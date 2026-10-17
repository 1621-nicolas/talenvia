# Migración de Talenvía: SQLite → Microsoft SQL Server

## Objetivo y alcance

**SQL Server es el motor principal de Talenvía**. Se mantiene Django 5.2, sus modelos y su ORM, la interfaz, los roles y las reglas ODS 10. SQLite solo queda como opción temporal de pruebas aisladas y para recuperar datos locales anteriores.

> Importante: la conexión `localhost` que aparece en SSMS identifica el motor instalado localmente. No se puede conectar al SQL Server de tu computadora desde un runner remoto de GitHub Actions sin configuraciones adicionales. El CI actual valida las funcionalidades en SQLite y que el motor `mssql` está disponible; no equivale a una prueba de integración real contra SQL Server.

## 1. Respaldar los archivos locales

Antes de modificar la base, copia y conserva en un lugar seguro:

- `db.sqlite3` (cuentas, empresas y ofertas anteriores).
- `private_uploads/` (archivos de CV cargados anteriormente).
- Tu `.env` local, si existía (no lo subas al repositorio).

La migración NO convierte automáticamente archivos de datos SQLite en SQL Server. Las migraciones Django crean el **esquema**; para conservar registros debes exportar/importar datos, como se muestra en el paso 6.

## 2. Crear la base en SQL Server Management Studio (SSMS)

Conecta a `localhost` con una cuenta que pueda crear bases de datos y ejecuta:

```sql
IF DB_ID(N'TalenviaDB') IS NULL
    CREATE DATABASE TalenviaDB;
GO
USE TalenviaDB;
GO
SELECT DB_NAME() AS BaseDeDatosActual;
GO
```

No crees las tablas manualmente. Django las creará con `migrate`.

## 3. Comprobar el ODBC Driver

En PowerShell:

```powershell
Get-OdbcDriver | Where-Object { $_.Name -like '*SQL Server*' }
```

Debes ver `ODBC Driver 18 for SQL Server` (recomendado). El hecho de tener SSMS no garantiza que el controlador 18 esté instalado. Consulta la documentación oficial de Microsoft si necesitas instalarlo.

## 4. Instalar dependencias y configurar la conexión

Desde la carpeta raíz del repositorio (actualiza los cambios):

```powershell
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

El archivo `.env` se carga automáticamente mediante `python-dotenv` y está excluido de GitHub.

### Opción A: Autenticación Windows (recomendada para desarrollo local)

Si tu cuenta de Windows tiene permisos sobre `TalenviaDB`:

```dotenv
DB_ENGINE=sqlserver
DB_NAME=TalenviaDB
DB_HOST=localhost
DB_PORT=
DB_AUTH=windows
DB_ODBC_DRIVER=ODBC Driver 18 for SQL Server
DB_TRUST_SERVER_CERTIFICATE=true
```

No uses `DB_USER` ni `DB_PASSWORD` en este modo. La identidad usada será la misma con la que ejecutas Python.

### Opción B: Autenticación SQL Server (usuario dedicado)

Si usas credenciales SQL, cambia tu archivo **local** `.env`:

```dotenv
DB_ENGINE=sqlserver
DB_NAME=TalenviaDB
DB_HOST=localhost
DB_PORT=
DB_AUTH=sqlserver
DB_USER=talenvia_app
DB_PASSWORD=REEMPLAZAR_CON_CONTRASENA_SEGURA
DB_TRUST_SERVER_CERTIFICATE=true
```

Para crear `talenvia_app` de forma opcional, un administrador puede ejecutar en SSMS lo siguiente, **sustituyendo** la contraseña ilustrativa por una realmente segura:

```sql
USE master;
GO
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'talenvia_app')
    CREATE LOGIN talenvia_app WITH PASSWORD = N'REEMPLAZAR_CON_CONTRASENA_SEGURA';
GO
USE TalenviaDB;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'talenvia_app')
    CREATE USER talenvia_app FOR LOGIN talenvia_app;
GO
-- Exclusivamente para ejecutar migraciones en la base académica local:
ALTER ROLE db_owner ADD MEMBER talenvia_app;
GO
```

Nunca uses `sa` para la conexión permanente de la aplicación ni compartas contraseñas por chat o GitHub. En producción se aplican permisos mínimos en vez de `db_owner`.

**Certificado**: `DB_TRUST_SERVER_CERTIFICATE=true` es solo para desarrollo local con un certificado autofirmado; en producción debes usar uno válido y `false`. El proyecto impide la opción insegura si `DJANGO_DEBUG=false`.

## 5. Crear tablas y probar SQL Server

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py sembrar_apoyos
.\.venv\Scripts\python.exe manage.py shell -c "from django.db import connection; connection.ensure_connection(); print(connection.vendor, connection.settings_dict['NAME'])"
```

Debe imprimirse `microsoft` (identificador del backend SQL Server) y `TalenviaDB`. Un error de conexión o migración significa que todavía no está validada la integración; comparte **solo el mensaje de error sin contraseñas**.

Para revisar las tablas en SSMS: **Bases de datos → TalenviaDB → Tablas**. Busca `empleo_usuario`, `empleo_empresa`, `empleo_ofertalaboral`, etc.

Si estás empezando con datos DEMO, ejecuta:

```powershell
.\.venv\Scripts\python.exe manage.py sembrar_demo --confirmar
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Estas cuatro ofertas son **ficticias**; se muestran para evaluación de interfaz, no representan oportunidades reales.

## 6. Migrar usuarios/ofertas existentes desde SQLite (opcional)

Si quieres conservar cuentas y ofertas de tu `db.sqlite3` anterior, hazlo **antes de crear datos de prueba o un superusuario nuevos en SQL Server**, para reducir conflictos de claves.

```powershell
# En la sesión actual, exporta desde la SQLite previa:
$env:DB_ENGINE = "sqlite"
.\.venv\Scripts\python.exe manage.py dumpdata empleo --natural-foreign --natural-primary --indent 2 --output respaldo_empleo.json

# Cambia de vuelta a SQL Server sin tocar tu .env:
$env:DB_ENGINE = "sqlserver"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py loaddata respaldo_empleo.json
.\.venv\Scripts\python.exe manage.py sembrar_apoyos
```

Conserva también `private_uploads/` en la misma ruta si existen CV: el JSON exportado contiene las referencias de archivos, pero **no** incluye el contenido binario del PDF. Borra o guarda el JSON exportado en una ubicación privada, porque incluye datos personales y hashes de contraseñas.

**No elimines `db.sqlite3` ni su respaldo** hasta comprobar todos los usuarios y postulaciones en SQL Server. Si aparecen conflictos de claves, no sobrescribas registros: revisa el error y el estado de los datos.

## 7. Plan de calidad para el curso

- Pruebas de modelo/servicios: siguen disponibles en CI con `DB_ENGINE=sqlite`.
- Pruebas de integración SQL Server: requieren conectarse al motor real y ejecutar migraciones/casos sobre una base de prueba aislada.
- Las comprobaciones ODS 10, accesibilidad WCAG y privacidad de CV se mantienen.
- **No declarar** la migración de datos o la integración SQL Server como verificada hasta que se ejecute el paso 5 y se comprueben resultados reales.

Fuentes de referencia: [Microsoft mssql-django](https://github.com/microsoft/mssql-django), [configuración de conexión](https://learn.microsoft.com/en-us/sql/connect/python/mssql-django/connection-options).


## 8. Endurecimiento ODS 10 — migración 0002

La migración \`empleo/migrations/0002_integridad_ods10.py\` incorpora:

- Verificación de perfiles pertenecientes al rol correcto, duplicados de RUC y CV de postulaciones inconsistentes.
- Unicidad de RUC no vacío mediante \`unique=True\` y \`null=True\`: se normalizan los RUC en blanco como \`NULL\` para permitir empresas pendientes. Antes se revisan duplicados y valores inválidos.
- Campo opcional \`detalle_accesibilidad\` para explicar la aplicación de los apoyos de cada oferta, sin pedir diagnósticos.
- \`consentimiento_fecha\` y \`consentimiento_version\` en las postulaciones.
- Índices adicionales para estado y fecha de ofertas, empresa y estado, y candidaturas por oferta y fecha.

**Preservación de datos:** la migración no elimina usuarios, empresas, ofertas ni CV. Solo convierte RUC vacíos/espacios en \`NULL\`. Si identifica perfiles con roles incorrectos, RUC repetidos/invalidos o una postulación cuyo CV no corresponde, detiene la migración. Debes resolver los datos manualmente tras realizar un respaldo.

Los consentimientos antiguos se marcan \`historico-sin-evidencia\` con fecha nula. Esa etiqueta NO equivale a una aceptación nueva ni atribuye consentimiento no probado.

### Copia de seguridad en SQL Server

En SSMS, ejecuta antes de \`migrate\` (ajusta el directorio a una ruta donde SQL Server tenga permisos):

\`\`\`sql
BACKUP DATABASE TalenviaDB
TO DISK = N'C:\SQLBackups\TalenviaDB_pre_0002.bak'
WITH INIT, CHECKSUM;
GO
\`\`\`

Debes comprobar que el servidor tenga acceso a la carpeta y que el archivo se haya creado. No ejecutes el backup sobre otro servidor o una ruta no accesible. Los archivos PDF privados también necesitan su copia independiente.

### Consultas de diagnóstico previas

\`\`\`sql
USE TalenviaDB;
GO
SELECT LTRIM(RTRIM(ruc)) AS ruc, COUNT(*) AS empresas
FROM empleo_empresa
WHERE NULLIF(LTRIM(RTRIM(ruc)), '') IS NOT NULL
GROUP BY LTRIM(RTRIM(ruc))
HAVING COUNT(*) > 1;
GO
SELECT p.id, u.rol
FROM empleo_postulante p
JOIN empleo_usuario u ON u.id = p.usuario_id
WHERE u.rol <> 'POSTULANTE';
GO
SELECT e.id, u.rol
FROM empleo_empresa e
JOIN empleo_usuario u ON u.id = e.usuario_id
WHERE u.rol <> 'EMPRESA';
GO
SELECT po.id, po.postulante_id, cv.postulante_id AS titular_cv
FROM empleo_postulacion po
JOIN empleo_curriculum cv ON cv.id = po.curriculum_id
WHERE cv.postulante_id <> po.postulante_id;
GO
\`\`\`

**Si ves resultados en esas consultas, no ignores las advertencias.** Conserva el respaldo y corrige los datos caso por caso.

### Aplicación controlada

\`\`\`powershell
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py showmigrations empleo
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
\`\`\`

En SSMS comprueba los campos y los índices. Verifica que la restricción de RUC exista en el SQL Server real: los índices filtrados y constraints son un área con limitaciones declaradas por \`mssql-django\`, así que **no consideramos completada la prueba de integración hasta ejecutarla localmente**.

### Pruebas específicas

\`\`\`powershell
.\.venv\Scripts\python.exe manage.py test empleo.tests_integridad_ods10 -v 2
.\.venv\Scripts\python.exe manage.py test empleo -v 2
\`\`\`

El test sobre SQL Server debe utilizar una base temporal de pruebas para evitar alterar los registros reales. Asegúrate de que el usuario SQL tenga los permisos necesarios sobre esa base. GitHub Actions continúa usando SQLite para pruebas automáticas remotas.
