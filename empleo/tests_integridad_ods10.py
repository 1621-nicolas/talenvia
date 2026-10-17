"""Pruebas del endurecimiento ODS 10: identidad, RUC, CV y consentimiento."""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import OfertaForm, PerfilEmpresaForm
from .models import Curriculum, Empresa, OfertaLaboral, Postulacion, Postulante, Usuario
from .services import CONSENTIMIENTO_VERSION


class IntegridadODS10TestCase(TestCase):
    def setUp(self):
        self.usuario_p = Usuario.objects.create_user(
            email="perfil@ejemplo.test", rol=Usuario.Rol.POSTULANTE, password="ClaveFuerte2026!")
        self.postulante = Postulante.objects.create(
            usuario=self.usuario_p, nombres="Persona de prueba", ubicacion="Trujillo")
        self.usuario_e = Usuario.objects.create_user(
            email="empresa-prueba@ejemplo.test", rol=Usuario.Rol.EMPRESA, password="ClaveEmpresa2026!")
        self.empresa = Empresa.objects.create(
            usuario=self.usuario_e, razon_social="Compañía Demo", ruc="12345678901",
            ubicacion="Trujillo", correo_contacto="contacto@ejemplo.test",
            estado=Empresa.Estado.APROBADA)
        self.oferta = OfertaLaboral.objects.create(
            empresa=self.empresa, titulo="Diseño accesible",
            descripcion="Diseño con inclusión", requisitos="Formación en diseño",
            detalle_accesibilidad="La empresa ofrece instrucciones escritas y reuniones remotas.",
            ubicacion="Trujillo", modalidad="REMOTO",
            fecha_cierre=timezone.localdate() + timedelta(days=15))

    def test_cambio_de_rol_con_perfil_existente_se_rechaza(self):
        self.usuario_p.rol = Usuario.Rol.EMPRESA
        with self.assertRaises(ValidationError):
            self.usuario_p.save()
        self.usuario_p.refresh_from_db()
        self.assertEqual(self.usuario_p.rol, Usuario.Rol.POSTULANTE)

    def test_creacion_de_perfil_con_rol_incompatible_falla(self):
        with self.assertRaises(ValidationError):
            Postulante.objects.create(usuario=self.usuario_e)
        with self.assertRaises(ValidationError):
            Empresa.objects.create(usuario=self.usuario_p)

    def test_ruc_duplicado_rechazado_en_base_de_datos(self):
        segundo = Usuario.objects.create_user(email="empresa2@ejemplo.test",
                                               password="ClaveEmpresa2026!", rol=Usuario.Rol.EMPRESA)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Empresa.objects.create(
                    usuario=segundo, razon_social="Otra compañía", ruc="12345678901")
        self.assertEqual(Empresa.objects.filter(ruc="12345678901").count(), 1)

    def test_empresas_pendientes_pueden_tener_ruc_vacio(self):
        nuevo = Usuario.objects.create_user(
            email="empresa3@ejemplo.test", password="ClaveEmpresa2026!", rol=Usuario.Rol.EMPRESA)
        Empresa.objects.create(usuario=nuevo)
        self.empresa.ruc = ""
        self.empresa.save()
        self.empresa.refresh_from_db()
        self.assertIsNone(self.empresa.ruc)
        self.assertFalse(self.empresa.completo)
        self.assertEqual(Empresa.objects.filter(ruc__isnull=True).count(), 2)

    def test_formulario_empresa_acepta_ruc_pendiente(self):
        form = PerfilEmpresaForm(data={
            "razon_social": "Empresa sin RUC", "ruc": "", "ubicacion": "",
            "correo_contacto": ""}, instance=self.empresa)
        self.assertTrue(form.is_valid(), form.errors.as_text())
        self.assertIsNone(form.cleaned_data["ruc"])

    def test_oferta_almacena_y_muestra_detalle_de_apoyos(self):
        self.assertIn("instrucciones escritas", self.oferta.detalle_accesibilidad)
        form = OfertaForm(instance=self.oferta)
        self.assertIn("detalle_accesibilidad", form.fields)
        respuesta = self.client.get(reverse("detalle_oferta", args=[self.oferta.pk]))
        self.assertContains(respuesta, "Cómo se brindan estos apoyos")
        self.assertContains(respuesta, "instrucciones escritas")

    def test_postulacion_no_acepta_cv_de_otro_postulante(self):
        otra_cuenta = Usuario.objects.create_user(
            email="otra-persona@ejemplo.test", rol=Usuario.Rol.POSTULANTE,
            password="ClavePersona2026!")
        otro_perfil = Postulante.objects.create(
            usuario=otra_cuenta, nombres="Otro perfil", ubicacion="Lima")
        cv_ajeno = Curriculum.objects.create(
            postulante=otro_perfil, archivo="cv/archivo-otra-persona.pdf",
            tamano_bytes=150, es_actual=True)
        with self.assertRaises(ValidationError):
            Postulacion.objects.create(
                postulante=self.postulante, oferta=self.oferta,
                curriculum=cv_ajeno, consentimiento=True,
                correo_contacto=self.usuario_p.email)
        self.assertEqual(Postulacion.objects.count(), 0)

    def test_postulacion_no_acepta_falta_de_consentimiento(self):
        cv = Curriculum.objects.create(
            postulante=self.postulante, archivo="cv/archivo.pdf",
            tamano_bytes=150, es_actual=True)
        with self.assertRaises(ValidationError):
            Postulacion.objects.create(
                postulante=self.postulante, oferta=self.oferta,
                curriculum=cv, consentimiento=False,
                correo_contacto=self.usuario_p.email)

    def test_servicio_registra_version_fecha_del_consentimiento(self):
        from .services import enviar_postulacion
        Curriculum.objects.create(
            postulante=self.postulante, archivo="cv/archivo.pdf",
            tamano_bytes=150, es_actual=True)
        inicio = timezone.now()
        post = enviar_postulacion(self.postulante, self.oferta, consentimiento=True)
        self.assertEqual(post.consentimiento_version, CONSENTIMIENTO_VERSION)
        self.assertIsNotNone(post.consentimiento_fecha)
        self.assertGreaterEqual(post.consentimiento_fecha, inicio)

    def test_indices_planificados(self):
        nombres_oferta = {i.name for i in OfertaLaboral._meta.indexes}
        nombres_postulacion = {i.name for i in Postulacion._meta.indexes}
        self.assertIn("idx_oferta_estado_fecha", nombres_oferta)
        self.assertIn("idx_oferta_empresa_estado", nombres_oferta)
        self.assertIn("idx_postulacion_oferta_fecha", nombres_postulacion)
