"""T2 — Ejercicio TDD: un filtro de apoyo inválido no debe ampliar resultados.

RED: primero se escriben estas pruebas sin cambiar el código de la vista.
GREEN: después se modifica exclusivamente la lógica del filtrado.
"""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Apoyo, Empresa, OfertaLaboral, Usuario


class TDDFiltroApoyoTestCase(TestCase):
    def setUp(self):
        cuenta = Usuario.objects.create_user(
            email="empresa-t2@ejemplo.test", password="ClaveSegura2026!",
            rol=Usuario.Rol.EMPRESA)
        empresa = Empresa.objects.create(
            usuario=cuenta, razon_social="DEMO empresa T2", ruc="12345678901",
            ubicacion="Trujillo", correo_contacto="empresa@ejemplo.test",
            estado=Empresa.Estado.APROBADA)
        self.apoyo = Apoyo.objects.create(
            nombre="Comunicación escrita", descripcion="Instrucciones documentadas")
        self.inactivo = Apoyo.objects.create(
            nombre="Apoyo desactivado", descripcion="No disponible", activo=False)
        self.oferta = OfertaLaboral.objects.create(
            empresa=empresa, titulo="Analista T2",
            descripcion="Trabajo de análisis", requisitos="Manejo básico de datos",
            ubicacion="Trujillo", modalidad=OfertaLaboral.Modalidad.REMOTO,
            fecha_cierre=timezone.localdate() + timedelta(days=20))
        self.oferta.apoyos.add(self.apoyo, self.inactivo)

    def test_t2_filtro_apoyo_inexistente_no_devuelve_todos_los_empleos(self):
        respuesta = self.client.get(reverse("ofertas"), {"apoyo": "999999"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["pagina"].paginator.count, 0)

    def test_t2_filtro_apoyo_desactivado_no_amplia_resultados(self):
        respuesta = self.client.get(reverse("ofertas"), {"apoyo": self.inactivo.pk})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["pagina"].paginator.count, 0)

    def test_t2_filtro_apoyo_valido_sigue_funcionando(self):
        respuesta = self.client.get(reverse("ofertas"), {"apoyo": self.apoyo.pk})
        self.assertEqual(respuesta.context["pagina"].paginator.count, 1)
