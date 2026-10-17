"""Pruebas automáticas básicas de las nuevas plantillas del Diseño 1."""
from django.test import TestCase
from django.urls import reverse


class DisenoInclusivoTestCase(TestCase):
    def test_inicio_incluye_busqueda_real_y_principios_ods10(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Tu talento merece oportunidades")
        self.assertContains(respuesta, 'aria-label="Buscar oportunidades laborales"')
        self.assertContains(respuesta, 'name="q"')
        self.assertContains(respuesta, 'name="ubicacion"')
        self.assertContains(respuesta, 'name="modalidad"')
        self.assertContains(respuesta, "ODS 10")
        self.assertContains(respuesta, "equipo-inclusivo.svg")

    def test_portada_sin_ofertas_no_inventa_candidatos_ni_puestos(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertContains(respuesta, "Aún no hay ofertas publicadas")
        self.assertNotContains(respuesta, "Analista de datos junior")

    def test_filtros_se_pueden_consultar_sin_registro(self):
        respuesta = self.client.get(reverse("ofertas"), {"q": "administración", "ubicacion": "Lima", "modalidad": "REMOTO"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "administración")
        self.assertContains(respuesta, "Lima")
        self.assertContains(respuesta, 'aria-label="Filtrar ofertas laborales"')
        self.assertContains(respuesta, "Apoyos de accesibilidad")

    def test_navegacion_tiene_salto_al_contenido_y_etiqueta(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertContains(respuesta, 'href="#contenido"')
        self.assertContains(respuesta, 'id="contenido"')
        self.assertContains(respuesta, 'aria-label="Navegación principal"')
