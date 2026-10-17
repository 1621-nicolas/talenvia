# Plan inicial de pruebas — Talenvía

**Objetivo:** validar la accesibilidad, la igualdad de oportunidades y la privacidad en Talenvía, conforme al ODS 10 y las prácticas de campo 01 y 02.

## Trazabilidad inicial

| Historia | Alcance | Evidencia esperada |
|---|---|---|
| HU01 | Registro y acceso | Correo único, roles permitidos, bloqueo de credenciales inválidas |
| HU02 | Permisos | Acceso denegado entre roles y perfiles ajenos |
| HU03 | Perfil postulante | Campos básicos, apoyos opcionales y privados |
| HU04 | CV | PDF real, tamaño máximo de 5 000 000 bytes, versiones y acceso |
| HU05 | Empresa | RUC, aprobación y suspensión |
| HU06 | Ofertas | Crear, editar antes de postulaciones y cerrar |
| HU07 | Búsqueda | Filtros AND, máximo 10 resultados por página, disponibilidad |
| HU08 | Postulaciones | Consentimiento, versiones, unicidad e historial |
| HU09 | Candidatos | Empresa propietaria, CV recibido y contacto externo |
| HU10 | Administración | Moderación, catálogo y ausencia de descarga administrativa |
| HU11 | Accesibilidad teclado | NVDA, foco visible, navegación sin ratón |
| HU12 | Legibilidad | Contraste, zoom al 200 % y errores claros |

## Pruebas automáticas incorporadas en la base inicial

- Pruebas Django de permisos cruzados, correo único, rol reservado, ofertas y filtros.
- Rechazo de PDF falso y archivos que exceden el límite.
- Aislamiento de CV entre postulantes y empresas.
- Conservación de versiones del CV y prevención de postulaciones duplicadas.
- Bloqueo de funciones para empresas pendientes y suspendidas.

## Evaluaciones pendientes de implementación y ejecución

- Completar cobertura de los 48 criterios de aceptación y registrar los casos con identificadores y evidencia.
- Automatización de navegador con Selenium o Playwright.
- Pruebas de rendimiento y estrés con k6/JMeter (100 ofertas; 20 búsquedas; meta de 19/20 en 2 s).
- Revisión manual con NVDA, zoom al 200 %, medición de contraste, WAVE/axe/Lighthouse.
- Análisis OWASP, métricas de defectos y refactorización.
- Preparación del paper y evidencia de contribución al ODS 10.

**Importante:** una prueba escrita o integrada en CI no equivale a un resultado aprobado hasta verificar su ejecución. No declarar certificación WCAG.
