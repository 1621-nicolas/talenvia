"""Registro manual de ofertas desde Django Admin y datos ficticios de demostración."""
from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Apoyo, Empresa, OfertaLaboral, Usuario


class OfertasAdministrativasTestCase(TestCase):
    def setUp(self):
        self.administrador = Usuario.objects.create_superuser(
            email="admin-ofertas@ejemplo.test", password="ContrasenaAdmin2026!"
        )
        self.empresa_usuario = Usuario.objects.create_user(
            email="empresa-admin@ejemplo.test", password="ContrasenaEmpresa2026!",
            rol=Usuario.Rol.EMPRESA,
        )
        self.empresa = Empresa.objects.create(
            usuario=self.empresa_usuario,
            razon_social="Empresa de prueba", ruc="12345678901",
            ubicacion="Trujillo", correo_contacto="contacto@ejemplo.test",
            estado=Empresa.Estado.APROBADA,
        )
        self.apoyo = Apoyo.objects.create(nombre="Acceso sin escalones", descripcion="Acceso al área sin escalones")
        self.client.force_login(self.administrador)

    def datos_oferta(self, **otros):
        datos = {
            "empresa": str(self.empresa.pk),
            "titulo": "Asistente de sistemas",
            "descripcion": "Puesto inclusivo de soporte informático",
            "requisitos": "Experiencia en informática",
            "ubicacion": "Trujillo",
            "modalidad": "REMOTO",
            "fecha_cierre": (timezone.localdate() + timedelta(days=30)).isoformat(),
            "apoyos": [str(self.apoyo.pk)],
            "estado": OfertaLaboral.Estado.PUBLICADA,
            "_save": "Guardar",
        }
        datos.update(otros)
        return datos

    def test_superusuario_puede_crear_oferta_manualmente(self):
        respuesta_get = self.client.get(reverse("admin:empleo_ofertalaboral_add"))
        self.assertEqual(respuesta_get.status_code, 200)
        respuesta_post = self.client.post(
            reverse("admin:empleo_ofertalaboral_add"), self.datos_oferta(),
        )
        self.assertEqual(respuesta_post.status_code, 302)
        self.assertEqual(OfertaLaboral.objects.count(), 1)
        self.assertEqual(OfertaLaboral.disponibles().count(), 1)
        self.assertEqual(
            list(OfertaLaboral.objects.first().apoyos.values_list("pk", flat=True)),
            [self.apoyo.pk],
        )
        self.assertContains(self.client.get(reverse("ofertas")), "Asistente de sistemas")

    def test_admin_rechaza_empresa_pendiente(self):
        self.empresa.estado = Empresa.Estado.PENDIENTE
        self.empresa.save(update_fields=["estado"])
        respuesta = self.client.post(reverse("admin:empleo_ofertalaboral_add"), self.datos_oferta())
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(OfertaLaboral.objects.count(), 0)

    def test_admin_rechaza_oferta_vencida(self):
        respuesta = self.client.post(reverse("admin:empleo_ofertalaboral_add"),
                                    self.datos_oferta(fecha_cierre=(timezone.localdate() - timedelta(days=1)).isoformat()))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(OfertaLaboral.objects.count(), 0)

    @override_settings(DEBUG=True)
    def test_sembrado_demo_no_duplica_las_ofertas(self):
        call_command("sembrar_demo", confirmar=True, verbosity=0)
        self.assertEqual(OfertaLaboral.disponibles().count(), 4)
        call_command("sembrar_demo", confirmar=True, verbosity=0)
        self.assertEqual(OfertaLaboral.disponibles().count(), 4)
        self.assertContains(self.client.get(reverse("ofertas")), "DEMO")
