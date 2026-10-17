# T2 — Matriz de casos de prueba (semana 9)

**Proyecto:** Talenvía · ODS 10. **Entorno:** QA/local con datos ficticios.
Una prueba definida no equivale a una prueba ejecutada. Registrar fecha, ambiente,
motor de BD, versión/commit, resultado real, evidencia y defecto asociado.

| ID | Tipo | Precondición | Acción / datos de entrada | Resultado esperado | Evidencia |
|---|---|---|---|---|---|
| UT01 | Unidad | Usuario de prueba | Registrar email repetido | El formulario rechaza duplicado | Django TestCase |
| UT02 | Unidad | PDF falso de prueba | Subir documento con cabecera incorrecta | Rechazo de CV | Django TestCase |
| IT01 | Integración | Empresa pendiente | Intentar crear oferta | No se guarda oferta | Django TestCase |
| IT02 | Integración | Postulante con CV | Postular dos veces a misma oferta | Un solo registro; segundo rechazado | Django TestCase |
| IT03 | Integración | Empresa B sin postulaciones a oferta A | Descargar CV de A | Acceso denegado | Django TestCase |
| TD01 | TDD / funcional | Oferta visible | GET /ofertas/?apoyo=999999 | Cero resultados | Ciclo RED→GREEN |
| TD02 | TDD / funcional | Apoyo desactivado | Filtrar por su ID | Cero resultados | Ciclo RED→GREEN |
| FT01 | Navegador | Servidor QA en marcha | Abrir inicio | Portada y buscador accesibles | Playwright captura |
| FT02 | Navegador | Servidor QA en marcha | Buscar «Analista» | URL mantiene filtro y muestra resultados | Playwright captura |
| FT03 | Navegador | Ofertas DEMO disponibles | Seleccionar REMOTO | Filtro aplicado | Playwright captura |
| FT04 | Navegador | Correo sintético nuevo | Registro postulante | Accede a panel propio | Playwright captura |
| FT05 | Navegador | Ofertas DEMO disponibles | Abrir una oferta | Muestra requisitos y apoyos | Playwright captura |
| FT06 | Accesibilidad básica | Navegador Chromium | Presionar Tab desde inicio | Enfoque en «Saltar al contenido» | Playwright captura |
| AT01 | Aceptación manual | Empresa aprobada y CV sintético | Enviar postulación autorizada | Empresa ve únicamente su solicitud | Capturas y firma del evaluador |
| AT02 | Aceptación manual | Empresa pendiente | Intentar publicar | Publicación bloqueada | Capturas y firma del evaluador |
| NF01 | No funcional | Servidor QA local | 2→5 usuarios virtuales durante 25 s | p95 <2 s; fallos <5 % | JSON/resumen k6 |
| NF02 | Accesibilidad manual | Navegador + NVDA | Navegar registro con teclado y lector | Etiquetas y errores comprensibles | Bitácora manual |

## Bitácora por prueba (rellenar tras cada ejecución)

- ID: 
- Fecha y responsable:
- Commit y motor de base de datos:
- Datos iniciales / precondiciones:
- Resultado esperado:
- Resultado obtenido:
- Estado: Aprobado / Fallido / Bloqueado / Pendiente
- Evidencia (ruta de captura, log o enlace a GitHub Actions):
- Defecto y severidad, si corresponde:
- Acción correctiva y repetición, si corresponde:

## Evidencias iniciales TDD

- RED — pruebas añadidas antes de corregir la vista: [ejecución con dos fallos esperados](https://github.com/1621-nicolas/talenvia/actions/runs/39015561913). Ambas devolvían 1 resultado cuando se esperaban 0.
- GREEN — ejecución de corrección: completar enlace a la ejecución después de confirmarla.
- **No falsificar** resultados manuales, de SQL Server ni de navegador. Conservar el contexto de SQLite del CI.
