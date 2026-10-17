# Identidad visual Talenvía — Diseño 1 (ODS 10)

## Decisión de diseño
Se adoptó la primera propuesta seleccionada: una interfaz **moderna e inclusiva** que combina un portal de empleo profesional con el estilo visual cálido y limpio de una startup. Las referencias son inspiración, no una copia de identidad ni de contenido de otros sitios.

## Sistema de diseño
- Color de acción principal: `#076571`; estado hover `#054954`.
- Tinta para títulos: `#102B44`; texto habitual: `#193447`; texto secundario `#405C6C`.
- Fondo claro: `#F8FBFC`; superficies blancas y menta `#E5F6F2`.
- Contraste y foco: contornos visibles `#BF5800` sobre fondos claros.
- Tarjetas con bordes suaves, 20 px de radio, espacios generosos y botones claramente etiquetados.
- Ilustración SVG propia con personas diversas y una persona usuaria de silla de ruedas. No se usan fotos de personas reales ni servicios externos.
- No mostrar cifras, certificaciones ni testimonios ficticios de inclusión.
- Tarjetas de empresas y ofertas cargadas desde Django; los ejemplos se siembran manualmente y están marcados como DEMO.

## Plantillas
- `base.html`: navegación, marca, mensajes, footer y salto al contenido.
- `inicio.html`: hero, búsqueda real, beneficios, ofertas disponibles y compromiso ODS 10.
- `ofertas.html`: filtros, chips de apoyo, resultados y paginación.
- `_tarjeta_oferta.html`: componente repetible para empleos.
- `detalle_oferta.html`: condiciones y consentimiento para compartir CV.
- `panel.html`: tarjetas de navegación por rol.
- Formularios restantes heredan los estilos generales.

## Requisitos ODS 10 / WCAG (validación por realizar)
- No solicitar diagnóstico ni certificado médico.
- Preferencias de apoyo privadas y opcionales; filtros por **apoyos ofrecidos**, no por discapacidad.
- Navegación por teclado con foco visible; salto a contenido, etiquetas para controles e información textual.
- Tipografías y layouts responsivos; adaptación a móvil y ampliación del texto.
- Comprobar contraste con herramientas (axe/Lighthouse/WAVE); evaluar NVDA y zoom 200 % manualmente.
- Registrar resultados reales y correcciones en las evidencias del curso. Ninguna de estas metas implica conformidad WCAG certificada.

## Manual de revisión visual
1. Ejecutar `python manage.py runserver`.
2. Abrir inicio, ofertas, detalle, registro, inicio de sesión y panel en anchos móvil y escritorio.
3. Usar Tab y Mayús+Tab sin ratón; revisar orden lógico y foco visible.
4. Probar zoom al 200 %; comprobar ausencia de recortes o desplazamiento horizontal no previsto.
5. Usar NVDA con teclado en el flujo de registro, búsqueda y postulación.
6. Medir contrastes, registrar evidencias y resultados de auditorías axe/Lighthouse.
