"""Pruebas de requisitos iniciales; se ampliarán hasta cubrir los 48 criterios."""
import tempfile
from datetime import timedelta
from pathlib import Path
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .forms import CurriculumForm, RegistroForm
from .models import Apoyo, Curriculum, Empresa, OfertaLaboral, Postulacion, Postulante, Usuario
from .services import enviar_postulacion, puede_descargar_cv


class TalenviaTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._archivos_temporales = tempfile.TemporaryDirectory()
        cls._media_config = override_settings(MEDIA_ROOT=Path(cls._archivos_temporales.name))
        cls._media_config.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_config.disable()
        cls._archivos_temporales.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.clave = "ContrasenaSegura2026!"
        self.usuario_p = Usuario.objects.create_user(email="persona@ejemplo.test", password=self.clave, rol=Usuario.Rol.POSTULANTE)
        self.perfil = Postulante.objects.create(usuario=self.usuario_p, nombres="Persona de prueba", ubicacion="Trujillo")
        self.otro_usuario = Usuario.objects.create_user(email="otra@ejemplo.test", password=self.clave, rol=Usuario.Rol.POSTULANTE)
        self.otro_perfil = Postulante.objects.create(usuario=self.otro_usuario, nombres="Otra persona", ubicacion="Lima")
        self.usuario_e = Usuario.objects.create_user(email="empresa@ejemplo.test", password=self.clave, rol=Usuario.Rol.EMPRESA)
        self.empresa = Empresa.objects.create(usuario=self.usuario_e, razon_social="Empresa prueba", ruc="12345678901", ubicacion="Trujillo", correo_contacto="contacto@ejemplo.test", estado=Empresa.Estado.APROBADA)
        self.usuario_e2 = Usuario.objects.create_user(email="otraempresa@ejemplo.test", password=self.clave, rol=Usuario.Rol.EMPRESA)
        self.empresa2 = Empresa.objects.create(usuario=self.usuario_e2, razon_social="Otra Empresa", ruc="23456789012", ubicacion="Lima", correo_contacto="contacto2@ejemplo.test", estado=Empresa.Estado.APROBADA)
        self.apoyo = Apoyo.objects.create(nombre="Acceso sin escalones", descripcion="Ingreso accesible")
        self.oferta = OfertaLaboral.objects.create(empresa=self.empresa, titulo="Analista junior", descripcion="Puesto inclusivo", requisitos="Manejo básico de sistemas", ubicacion="Trujillo", modalidad=OfertaLaboral.Modalidad.REMOTO, fecha_cierre=timezone.localdate() + timedelta(days=5))
        self.oferta.apoyos.add(self.apoyo)

    def cv_valido(self):
        return SimpleUploadedFile("ejemplo.pdf", b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF", content_type="application/pdf")

    def crear_cv(self):
        return Curriculum.objects.create(postulante=self.perfil, archivo=self.cv_valido(), tamano_bytes=35, es_actual=True)

    def test_registro_publico_no_acepta_administrador(self):
        form = RegistroForm(data={"email": "nuevo@ejemplo.test", "rol": "ADMINISTRADOR", "password1": self.clave, "password2": self.clave})
        self.assertFalse(form.is_valid())
        self.assertIn("rol", form.errors)

    def test_correo_normalizado_y_unico(self):
        self.assertEqual(self.usuario_p.email, "persona@ejemplo.test")
        form = RegistroForm(data={"email": "PERSONA@ejemplo.test", "rol": "POSTULANTE", "password1": self.clave, "password2": self.clave})
        self.assertFalse(form.is_valid())

    def test_empresa_pendiente_no_publica(self):
        self.empresa.estado = Empresa.Estado.PENDIENTE
        self.empresa.save()
        self.client.force_login(self.usuario_e)
        respuesta = self.client.post(reverse("crear_oferta"), {})
        self.assertRedirects(respuesta, reverse("perfil_empresa"))
        self.assertEqual(OfertaLaboral.objects.count(), 1)
        self.assertFalse(OfertaLaboral.disponibles().exists())

    def test_postulante_no_publica_por_url_directa(self):
        self.client.force_login(self.usuario_p)
        respuesta = self.client.post(reverse("crear_oferta"), {})
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(OfertaLaboral.objects.count(), 1)

    def test_empresa_no_puede_postular(self):
        self.client.force_login(self.usuario_e)
        respuesta = self.client.post(reverse("postular", args=[self.oferta.pk]), {"acepto": "on"})
        self.assertEqual(respuesta.status_code, 403)

    def test_filtros_y_visibilidad_ofertas(self):
        r = self.client.get(reverse("ofertas"), {"modalidad": "REMOTO", "ubicacion": "Trujillo", "apoyo": self.apoyo.pk})
        self.assertContains(r, "Analista junior")
        r = self.client.get(reverse("ofertas"), {"modalidad": "PRESENCIAL"})
        self.assertNotContains(r, "Analista junior")
        self.oferta.estado = OfertaLaboral.Estado.CERRADA
        self.oferta.save()
        self.assertFalse(OfertaLaboral.disponibles().exists())

    def test_pdf_falso_y_limite_rechazados(self):
        falso = SimpleUploadedFile("falso.pdf", b"Esto no es un documento PDF", content_type="application/pdf")
        form = CurriculumForm(files={"archivo": falso})
        self.assertFalse(form.is_valid())
        demasiado_grande = SimpleUploadedFile("grande.pdf", b"%PDF-" + b"A" * 4_999_991 + b"%%EOF")
        form = CurriculumForm(files={"archivo": demasiado_grande})
        self.assertFalse(form.is_valid())

    def test_cv_privado_entre_postulantes(self):
        cv = self.crear_cv()
        self.client.force_login(self.otro_usuario)
        r = self.client.get(reverse("descargar_cv", args=[cv.pk]))
        self.assertEqual(r.status_code, 403)
        self.assertFalse(puede_descargar_cv(self.otro_usuario, cv))
        self.client.force_login(self.usuario_p)
        r = self.client.get(reverse("descargar_cv", args=[cv.pk]))
        self.assertEqual(r.status_code, 200)

    def test_postular_una_sola_vez_con_version_y_contacto(self):
        cv = self.crear_cv()
        registro = enviar_postulacion(self.perfil, self.oferta, consentimiento=True)
        self.assertEqual(registro.curriculum_id, cv.pk)
        self.assertEqual(registro.correo_contacto, "persona@ejemplo.test")
        with self.assertRaises(ValidationError):
            enviar_postulacion(self.perfil, self.oferta, consentimiento=True)
        self.assertEqual(Postulacion.objects.count(), 1)

    def test_empresa_ajena_no_accede_a_cv_ni_candidatos(self):
        cv = self.crear_cv()
        enviar_postulacion(self.perfil, self.oferta, consentimiento=True)
        self.client.force_login(self.usuario_e2)
        self.assertEqual(self.client.get(reverse("descargar_cv", args=[cv.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("candidatos", args=[self.oferta.pk])).status_code, 404)
        self.client.force_login(self.usuario_e)
        self.assertEqual(self.client.get(reverse("descargar_cv", args=[cv.pk])).status_code, 200)

    def test_empresa_suspendida_no_ve_candidatos(self):
        self.crear_cv()
        enviar_postulacion(self.perfil, self.oferta, consentimiento=True)
        self.empresa.estado = Empresa.Estado.SUSPENDIDA
        self.empresa.save()
        self.client.force_login(self.usuario_e)
        self.assertRedirects(self.client.get(reverse("candidatos", args=[self.oferta.pk])), reverse("perfil_empresa"))
        self.assertFalse(OfertaLaboral.disponibles().exists())

    def test_consentimiento_obligatorio(self):
        self.crear_cv()
        with self.assertRaises(ValidationError):
            enviar_postulacion(self.perfil, self.oferta, consentimiento=False)
        self.assertEqual(Postulacion.objects.count(), 0)

    def test_postulacion_conserva_version_anterior(self):
        primero = self.crear_cv()
        registro = enviar_postulacion(self.perfil, self.oferta, consentimiento=True)
        primero.es_actual = False
        primero.save(update_fields=["es_actual"])
        segundo = Curriculum.objects.create(postulante=self.perfil, archivo=self.cv_valido(), tamano_bytes=35, es_actual=True)
        registro.refresh_from_db()
        self.assertEqual(registro.curriculum_id, primero.pk)
        self.assertNotEqual(registro.curriculum_id, segundo.pk)
