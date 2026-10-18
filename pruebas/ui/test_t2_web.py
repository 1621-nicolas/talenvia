"""Pruebas funcionales T2 con navegador Chromium real (Playwright).

Requiere que Talenvía esté ejecutándose en BASE_URL. No usa cuentas reales.
Las capturas se guardan en resultados/t2/ui/ y se excluyen de Git.
"""
import os
import re
import unittest
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
CAPTURAS = Path("resultados/t2/ui")


class PruebasWebT2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        CAPTURAS.mkdir(parents=True, exist_ok=True)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 900}, locale="es-PE"
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(10000)

    def tearDown(self):
        self.context.close()

    def captura(self, nombre):
        self.page.screenshot(path=str(CAPTURAS / (nombre + ".png")), full_page=True)

    def test_ft01_portada_muestra_enfoque_ods10_y_busqueda(self):
        response = self.page.goto(BASE_URL + "/")
        self.assertEqual(response.status, 200)
        expect(self.page.get_by_role("heading", name=re.compile("Tu talento merece"))).to_be_visible()
        expect(self.page.get_by_role("searchbox", name="Puesto o palabra clave")).to_be_visible()
        expect(self.page.get_by_text("ODS 10", exact=False).first).to_be_visible()
        self.captura("FT01_portada")

    def test_ft02_busqueda_desde_portada(self):
        self.page.goto(BASE_URL + "/")
        self.page.locator("form.busqueda-form input[name=q]").fill("Analista")
        self.page.locator("form.busqueda-form button[type=submit]").click()
        self.page.wait_for_url(re.compile(r"/ofertas/\?"))
        self.assertIn("q=Analista", self.page.url)
        expect(self.page.get_by_role("heading", name=re.compile("Explora empleos"))).to_be_visible()
        self.captura("FT02_busqueda")

    def test_ft03_filtrar_por_modalidad(self):
        self.page.goto(BASE_URL + "/ofertas/")
        self.page.locator("form.filtros select[name=modalidad]").select_option("REMOTO")
        self.page.locator("form.filtros button[type=submit]").click()
        self.assertIn("modalidad=REMOTO", self.page.url)
        expect(self.page.get_by_role("heading", name="Oportunidades disponibles")).to_be_visible()
        self.captura("FT03_modalidad")

    def test_ft04_registro_postulante_y_panel(self):
        self.page.goto(BASE_URL + "/registro/")
        self.page.locator('input[name="email"]').fill(
            "prueba-t2-" + uuid.uuid4().hex[:12] + "@ejemplo.test"
        )
        self.page.locator('select[name="rol"]').select_option("POSTULANTE")
        self.page.locator('input[name="password1"]').fill("ClaveFuerteTalenvia2026!")
        self.page.locator('input[name="password2"]').fill("ClaveFuerteTalenvia2026!")
        self.page.get_by_role("button", name="Registrarme").click()
        self.page.wait_for_url("**/panel/")
        expect(self.page.get_by_role("heading", name=re.compile("Bienvenido"))).to_be_visible()
        self.captura("FT04_registro_panel")

    def test_ft05_detalle_oferta_si_hay_demo(self):
        self.page.goto(BASE_URL + "/ofertas/")
        tarjetas = self.page.locator(".tarjeta-oferta .tarjeta-enlace")
        self.assertGreater(tarjetas.count(), 0, "Carga ofertas DEMO en esta base de PRUEBAS")
        tarjetas.first.click()
        expect(self.page.get_by_role("heading", name="Acerca del puesto")).to_be_visible()
        expect(self.page.get_by_role("heading", name="Apoyos y condiciones de accesibilidad")).to_be_visible()
        self.captura("FT05_detalle_oferta")

    def test_ft06_enlace_para_saltar_al_contenido_con_teclado(self):
        self.page.goto(BASE_URL + "/")
        self.page.keyboard.press("Tab")
        self.assertEqual(
            self.page.evaluate("document.activeElement.getAttribute('href')"), "#contenido"
        )
        self.captura("FT06_teclado")


if __name__ == "__main__":
    unittest.main(verbosity=2)
