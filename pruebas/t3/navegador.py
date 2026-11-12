"""Ejecutar con un servidor Django local que tenga datos DEMO."""
import argparse
import json
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright

BASE = "http://127.0.0.1:8000"
RUTAS = {"/": "inicio", "/ofertas/": "ofertas", "/registro/": "registro", "/ingresar/": "ingresar"}


class NavegacionT3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.salida = Path("resultados/t3") / args.motor
        cls.salida.mkdir(parents=True, exist_ok=True)
        cls.pw = sync_playwright().start()
        cls.browser = getattr(cls.pw, args.motor).launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.contexto = self.browser.new_context(viewport={"width": 1280, "height": 900}, locale="es-PE")
        self.addCleanup(self.contexto.close)
        self.pagina = self.contexto.new_page()

    def test_buscar_y_abrir_oferta(self):
        self.pagina.goto(BASE)
        self.pagina.get_by_role("searchbox", name="Puesto o palabra clave").fill("Analista")
        self.pagina.get_by_role("button", name="Buscar empleos").click()
        self.pagina.wait_for_url("**/ofertas/?**")
        self.assertIn("q=Analista", self.pagina.url)
        tarjeta = self.pagina.locator(".tarjeta-enlace").first
        expect(tarjeta).to_be_visible()
        tarjeta.click()
        expect(self.pagina.get_by_role("heading", name="Acerca del puesto")).to_be_visible()

    def test_salto_con_teclado_y_busqueda_sin_mouse(self):
        self.pagina.goto(BASE + "/ofertas/")
        self.pagina.keyboard.press("Tab")
        expect(self.pagina.locator("a.saltar")).to_be_focused()
        self.pagina.keyboard.press("Enter")
        expect(self.pagina.locator("#contenido")).to_be_focused()
        for _ in range(25):
            self.pagina.keyboard.press("Tab")
            if self.pagina.locator("#q").evaluate("el => el === document.activeElement"):
                break
        expect(self.pagina.locator("#q")).to_be_focused()
        self.pagina.keyboard.type("Analista")
        self.pagina.keyboard.press("Enter")
        self.pagina.wait_for_url("**/ofertas/?**")
        self.assertIn("q=Analista", self.pagina.url)
        expect(self.pagina.locator(".tarjeta-enlace").first).to_be_visible()

    def test_reflujo_a_640_y_320_css_px(self):
        for ancho in (640, 320):
            self.pagina.set_viewport_size({"width": ancho, "height": 800})
            for ruta, nombre in RUTAS.items():
                with self.subTest(ancho=ancho, ruta=ruta):
                    self.pagina.goto(BASE + ruta)
                    medidas = self.pagina.evaluate("() => [document.documentElement.scrollWidth, innerWidth]")
                    self.pagina.screenshot(path=self.salida/f"{nombre}-{ancho}.png", full_page=True)
                    self.assertLessEqual(medidas[0], medidas[1]+1, medidas)
                    expect(self.pagina.get_by_role("heading", level=1)).to_be_visible()

    def test_axe_en_cuatro_paginas(self):
        if args.axe is None:
            self.skipTest("Se requiere la distribución local de axe-core")
        for ruta, nombre in RUTAS.items():
            with self.subTest(ruta=ruta):
                self.pagina.goto(BASE + ruta)
                self.pagina.add_script_tag(path=args.axe)
                datos = self.pagina.evaluate("async () => await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})")
                (self.salida/f"axe-{nombre}.json").write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
                resumen = [(v["id"], v["impact"], len(v["nodes"])) for v in datos["violations"]]
                print(f"AXE {nombre} {resumen}", flush=True)
                self.assertFalse(resumen, f"Reglas con infracciones: {resumen}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--motor", choices=["chromium", "firefox", "webkit"], required=True)
    parser.add_argument("--axe")
    args = parser.parse_args()
    unittest.main(argv=["navegador.py"], verbosity=2)
