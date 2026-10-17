# Alcance T2, hasta la semana 9 — Calidad y Pruebas de Software

## Correspondencia con la rúbrica (máximo 20 puntos)

1. **Introducción y antecedentes (4 pt):** problemática de barreras de acceso a empleos inclusivos, contexto peruano, contribución a ODS 10, metas 10.2 y 10.3. Preparar **cinco antecedentes confiables** con análisis crítico y vínculos verificables. No inventar datos de empleabilidad ni impacto.
2. **Análisis del problema y objetivos (4 pt):** Ishikawa con causas agrupadas en personas, procesos, tecnología, información, contexto institucional y accesibilidad; pregunta general y específicas, propuestas de solución, objetivos medibles que incluyan historias HU01-HU12, criterios de aceptación y pruebas de calidad. Los tipos de pruebas futuros pueden figurar como objetivos, sin afirmar que ya se ejecutaron.
3. **Herramientas y estándares (4 pt):** justificar Django TestCase (unidad/integración), coverage (cobertura), Playwright (interfaz), k6 (rendimiento), GitHub Actions (CI), SQL Server (persistencia), ISO/IEC 25010 (calidad de producto) y WCAG 2.2 (accesibilidad). Comparar alternativas antes de seleccionar; no confundir herramienta, estándar y metodología.
4. **Unitarias, integración y TDD (4 pt):** mostrar resultados Django, cobertura y casos límite; demostrar RED→GREEN del filtro de apoyos con dos commits y ejecuciones. La CI automatizada con SQLite NO prueba integración real con SQL Server. Esa integración se verifica en un entorno SQL Server de PRUEBAS aislado.
5. **Funcionales, aceptación y no funcionales (4 pt):** casos documentados, Playwright para la interfaz, aceptación manual firmada por la persona evaluadora, prueba ligera con k6, métricas p95 y porcentaje de fallos, evidencias y defectos.

## Qué no necesitamos terminar ahora

- Auditoría exhaustiva de seguridad/OWASP, análisis SonarQube final, paper final.
- Alta concurrencia/estrés extremo, evaluaciones finales de conformidad WCAG.
- Todos los 48 criterios de aceptación automatizados: conservar trazabilidad y priorizar flujo crítico.
- Despliegue en producción o integración continua contra la base personal SQL Server.

## Ejecución segura

Usar **datos DEMO**. El directorio `resultados/` contendrá capturas y salidas automáticas; no publicarlo con datos personales. Las ofertas de demostración no prueban impacto social real.

### A. Unitarias e integración

```powershell
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DB_ENGINE="sqlite"
.\.venv\Scripts\python.exe -m coverage run --source=empleo manage.py test empleo -v 2
.\.venv\Scripts\python.exe -m coverage report -m
```

Para **SQL Server**, después de configurar permisos para crear una base temporal de ensayo, ejecutar explícitamente `$env:DB_ENGINE="sqlserver"` y `manage.py test empleo`, que crea una base de datos de pruebas. No ejecutar pruebas de escritura manualmente contra `TalenviaDB` real.

### B. Navegador Playwright

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-t2.txt
.\.venv\Scripts\python.exe -m playwright install chromium
$env:DB_ENGINE="sqlite"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py sembrar_demo --confirmar
.\.venv\Scripts\python.exe manage.py runserver
```

En una **segunda terminal** en la misma carpeta:

```powershell
$env:BASE_URL="http://127.0.0.1:8000"
.\.venv\Scripts\python.exe -m unittest discover -s pruebas/ui -p "test_*.py" -v
```

Para evitar modificar tu base de datos SQL Server local, estas pruebas de navegador deben ejecutarse con una base SQLite de DEMO o una base QA aislada. Se guarda evidencia en `resultados/t2/ui/`.

### C. Rendimiento k6

Instalar Grafana k6, dejar el servidor QA en marcha y ejecutar:

```powershell
New-Item -ItemType Directory -Force resultados\t2 | Out-Null
k6 run --summary-export resultados\t2\k6-t2.json pruebas\rendimiento\t2_carga.js
```

Este ensayo controlado utiliza 2–5 usuarios virtuales por 25 segundos. No es prueba de estrés ni representa métricas de producción. Comparar p95 con 2000 ms y fallos con 5 %, informar los resultados observados, no los umbrales como si fueran mediciones.

### D. Reporte

Usar [matriz de casos](T2_CASOS_PRUEBA.md). Incluir registros de defectos, capturas, resultados automáticos, métricas y un anexo de revisión manual con NVDA (si se realiza). Revisar que los cinco antecedentes sean reales y estén citados.
