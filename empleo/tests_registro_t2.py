"""Pruebas T2 — registro inclusivo y navegación en todos los roles."""
from django.test import TestCase
from django.urls import reverse
from .forms import RegistroForm
from .models import Empresa, Postulante, Usuario


class RegistroYRegresoT2Tests(TestCase):
    password = "ContrasenaSegura2026!"

    def datos_empresa(self, **cambios):
        datos = {
            "rol": Usuario.Rol.EMPRESA,
            "email": "empresa-nueva@ejemplo.test",
            "razon_social": "Soluciones Inclusivas del Norte SAC",
            "ruc": "20601234567",
            "ubicacion": "Trujillo, La Libertad",
            "correo_contacto": "rrhh@ejemplo.test",
            "password1": self.password,
            "password2": self.password,
        }
        datos.update(cambios)
        return datos

    def test_empresa_se_registra_con_datos_basicos_y_pendiente(self):
        respuesta = self.client.post(reverse("registro"), self.datos_empresa())
        self.assertRedirects(respuesta, reverse("panel"))
        usuario = Usuario.objects.get(email="empresa-nueva@ejemplo.test")
        self.assertEqual(usuario.rol, Usuario.Rol.EMPRESA)
        empresa = usuario.perfil_empresa
        self.assertEqual(empresa.razon_social, "Soluciones Inclusivas del Norte SAC")
        self.assertEqual(empresa.ruc, "20601234567")
        self.assertEqual(empresa.ubicacion, "Trujillo, La Libertad")
        self.assertEqual(empresa.correo_contacto, "rrhh@ejemplo.test")
        self.assertEqual(empresa.estado, Empresa.Estado.PENDIENTE)
        self.assertFalse(empresa.habilitada)
        self.assertContains(self.client.get(reverse("panel")), "Pendiente")

    def test_registro_empresa_rechaza_datos_obligatorios_faltantes(self):
        respuesta = self.client.post(reverse("registro"), self.datos_empresa(
            razon_social="", ruc="", ubicacion="", correo_contacto=""))
        self.assertEqual(respuesta.status_code, 200)
        for campo in ("razon_social", "ruc", "ubicacion", "correo_contacto"):
            self.assertIn(campo, respuesta.context["form"].errors)
        self.assertFalse(Usuario.objects.filter(email="empresa-nueva@ejemplo.test").exists())

    def test_registro_empresa_rechaza_ruc_incorrecto(self):
        formulario = RegistroForm(data=self.datos_empresa(ruc="1234AB"))
        self.assertFalse(formulario.is_valid())
        self.assertIn("ruc", formulario.errors)

    def test_registro_empresa_rechaza_ruc_repetido(self):
        anterior = Usuario.objects.create_user(
            email="registrada@ejemplo.test",
            password=self.password, rol=Usuario.Rol.EMPRESA,
        )
        Empresa.objects.create(usuario=anterior, ruc="20601234567")
        formulario = RegistroForm(data=self.datos_empresa())
        self.assertFalse(formulario.is_valid())
        self.assertIn("ruc", formulario.errors)

    def test_registro_postulante_no_exige_datos_empresariales(self):
        datos = {
            "rol": Usuario.Rol.POSTULANTE,
            "email": "persona-nueva@ejemplo.test",
            "password1": self.password,
            "password2": self.password,
        }
        respuesta = self.client.post(reverse("registro"), datos)
        self.assertRedirects(respuesta, reverse("panel"))
        usuario = Usuario.objects.get(email="persona-nueva@ejemplo.test")
        self.assertTrue(Postulante.objects.filter(usuario=usuario).exists())
        self.assertFalse(Empresa.objects.filter(usuario=usuario).exists())

    def test_no_se_acepta_rol_administrador_mediante_registro(self):
        formulario = RegistroForm(data=self.datos_empresa(rol="ADMINISTRADOR"))
        self.assertFalse(formulario.is_valid())
        self.assertIn("rol", formulario.errors)

    def test_enlace_para_empresas_preselecciona_su_rol(self):
        respuesta = self.client.get(reverse("registro") + "?tipo=empresa")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["form"].initial["rol"], Usuario.Rol.EMPRESA)
        self.assertContains(respuesta, 'id="datos-empresa"')
        self.assertContains(respuesta, "Razón social")
        self.assertContains(respuesta, "Volver al inicio")

    def test_registro_inicio_sesion_y_empleos_tienen_regreso(self):
        for destino in ("registro", "login", "ofertas"):
            with self.subTest(pagina=destino):
                respuesta = self.client.get(reverse(destino))
                self.assertContains(respuesta, 'aria-label="Regresar"')
                self.assertContains(respuesta, 'href="/"')

    def test_inicio_sesion_solo_exige_correo_y_contrasena(self):
        cuenta = Usuario.objects.create_user(
            email="empresa-registrada@ejemplo.test",
            password=self.password, rol=Usuario.Rol.EMPRESA)
        Empresa.objects.create(
            usuario=cuenta, razon_social="Empresa Existente",
            ruc="20609998887", ubicacion="Lima",
            correo_contacto="contacto@ejemplo.test",
        )
        respuesta = self.client.post(reverse("login"), {
            "username": "empresa-registrada@ejemplo.test",
            "password": self.password,
        })
        self.assertRedirects(respuesta, reverse("panel"))
