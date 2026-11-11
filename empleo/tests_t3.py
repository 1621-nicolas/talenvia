"""Regresiones de privacidad, sesión y tratamiento de entradas en Talenvía."""
from datetime import timedelta
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from .models import Curriculum, Empresa, OfertaLaboral, Postulante, Usuario


class ControlesT3(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.persona = Usuario.objects.create_user(
            email="qa-persona@example.test", rol=Usuario.Rol.POSTULANTE)
        cls.perfil = Postulante.objects.create(
            usuario=cls.persona, nombres="Persona QA", ubicacion="Trujillo")
        cuenta = Usuario.objects.create_user(email="qa-empresa@example.test", rol=Usuario.Rol.EMPRESA)
        empresa = Empresa.objects.create(usuario=cuenta, razon_social="Empresa QA", ruc="20444444444",
                                        ubicacion="Trujillo", correo_contacto=cuenta.email,
                                        estado=Empresa.Estado.APROBADA)
        cls.oferta = OfertaLaboral.objects.create(
            empresa=empresa, titulo="Analista O'Reilly", descripcion="Prueba de búsqueda",
            requisitos="Análisis", ubicacion="Trujillo", modalidad="REMOTO",
            fecha_cierre=timezone.localdate() + timedelta(days=5))

    def test_busqueda_literal_con_apostrofo(self):
        for texto, cantidad in [("O'Reilly", 1), ("O'Neill", 0), ("100%", 0)]:
            with self.subTest(texto=texto):
                respuesta = self.client.get(reverse("ofertas"), {"q": texto})
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.context["pagina"].paginator.count, cantidad)
        self.assertEqual(OfertaLaboral.objects.count(), 1)

    def test_texto_reflejado_escapa_delimitadores_html(self):
        texto = 'Diseño <QA> & "ventas"'
        respuesta = self.client.get(reverse("ofertas"), {"q": texto})
        self.assertContains(respuesta, f'value="{escape(texto)}"')
        self.assertNotContains(respuesta, texto)

    def test_csrf_postulacion_con_y_sin_token(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.persona)
        Curriculum.objects.create(postulante=self.perfil, archivo="cv/qa.pdf", tamano_bytes=42, es_actual=True)
        pagina = cliente.get(reverse("detalle_oferta", args=[self.oferta.pk]))
        self.assertEqual(pagina.status_code, 200)
        ruta = reverse("postular", args=[self.oferta.pk])
        self.assertEqual(cliente.post(ruta, {"acepto": "on"}).status_code, 403)
        self.assertEqual(self.oferta.postulaciones.count(), 0)
        datos = {"acepto": "on", "csrfmiddlewaretoken": cliente.cookies["csrftoken"].value}
        self.assertRedirects(cliente.post(ruta, datos), reverse("mis_postulaciones"))
        self.assertEqual(self.oferta.postulaciones.count(), 1)

    def test_rutas_de_empresa_por_rol(self):
        sesion = self.client
        rutas = [reverse("mis_ofertas"), reverse("crear_oferta"), reverse("candidatos", args=[self.oferta.pk])]
        for url in rutas:
            with self.subTest(url=url, rol="anonimo"):
                self.assertRedirects(sesion.get(url), f"{reverse('login')}?next={url}")
        sesion.force_login(self.persona)
        for url in rutas:
            with self.subTest(url=url, rol="postulante"):
                self.assertEqual(sesion.get(url).status_code, 403)
        sesion.force_login(self.oferta.empresa.usuario)
        for url in rutas:
            with self.subTest(url=url, rol="empresa titular"):
                self.assertEqual(sesion.get(url).status_code, 200)

    def test_sesion_termina_al_cerrar(self):
        self.client.force_login(self.persona)
        self.assertEqual(self.client.get(reverse("panel")).status_code, 200)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("inicio"))
        self.assertRedirects(self.client.get(reverse("panel")), f"{reverse('login')}?next=/panel/")

    def test_cabeceras_y_cookie_en_configuracion_https(self):
        # Usa el cliente HTTPS y los ajustes del módulo de producción en la CI específica.
        respuesta = self.client.get(reverse("login"), secure=True)
        self.assertEqual(respuesta["X-Content-Type-Options"], "nosniff")
        self.assertEqual(respuesta["X-Frame-Options"], "DENY")
        self.assertEqual(respuesta.cookies["csrftoken"]["samesite"], "Lax")
        from django.conf import settings
        self.assertEqual(bool(respuesta.cookies["csrftoken"]["secure"]), settings.CSRF_COOKIE_SECURE)

    def test_cv_privado_con_descarga_y_cache(self):
        contenido = b"%PDF-1.4\nQA\n%%EOF"
        with TemporaryDirectory() as carpeta, self.settings(MEDIA_ROOT=carpeta):
            cv = Curriculum.objects.create(
                postulante=self.perfil, archivo=SimpleUploadedFile("qa.pdf", contenido),
                tamano_bytes=len(contenido), es_actual=True)
            ruta = reverse("descargar_cv", args=[cv.pk])
            self.client.force_login(self.oferta.empresa.usuario)
            self.assertEqual(self.client.get(ruta).status_code, 403)
            self.client.force_login(self.persona)
            respuesta = self.client.get(ruta)
            self.assertEqual(respuesta.status_code, 200)
            self.assertEqual(respuesta["Cache-Control"], "private, no-store")
            self.assertIn("attachment", respuesta["Content-Disposition"])
            self.assertEqual(b"".join(respuesta.streaming_content), contenido)

    def test_administracion_requiere_personal(self):
        url = reverse("admin:index")
        for usuario in (self.persona, self.oferta.empresa.usuario):
            with self.subTest(rol=usuario.rol):
                self.client.force_login(usuario)
                self.assertRedirects(self.client.get(url), f"{reverse('admin:login')}?next={url}")
