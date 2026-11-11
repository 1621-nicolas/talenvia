"""Verifica zoom real del navegador con chrome.tabs.setZoom en un perfil temporal."""
import json
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

salida = Path("resultados/t3/zoom")
salida.mkdir(parents=True, exist_ok=True)
extension = Path(__file__).with_name("zoom").resolve()
resultados = []
with tempfile.TemporaryDirectory() as perfil, sync_playwright() as pw:
    contexto = pw.chromium.launch_persistent_context(
        perfil, channel="chromium", headless=False, no_viewport=True,
        args=["--window-size=1280,900", f"--disable-extensions-except={extension}", f"--load-extension={extension}"])
    try:
        worker = (contexto.service_workers or [contexto.wait_for_event("serviceworker")])[0]
        p = contexto.pages[0]
        for ruta, nombre in [("/", "inicio"), ("/ofertas/", "ofertas"), ("/registro/", "registro"), ("/ingresar/", "ingresar")]:
            p.goto("http://127.0.0.1:8000" + ruta)
            zoom = worker.evaluate("""async () => {
                const [tab] = await chrome.tabs.query({url:'http://127.0.0.1/*'});
                await chrome.tabs.setZoom(tab.id, 2);
                return await chrome.tabs.getZoom(tab.id);
            }""")
            assert zoom == 2, zoom
            p.wait_for_function("window.devicePixelRatio >= 1.99")
            dimensiones = p.evaluate("() => ({vista: innerWidth, contenido: document.documentElement.scrollWidth, dpr: devicePixelRatio})")
            expect(p.get_by_role("heading", level=1)).to_be_visible()
            if ruta == "/ofertas/":
                p.get_by_role("searchbox", name="Palabra clave").fill("Analista")
                p.get_by_role("button", name="Aplicar filtros").click()
                expect(p.locator(".tarjeta-enlace").first).to_be_visible()
            p.screenshot(path=salida/f"{nombre}.png", full_page=True)
            resultados.append(dict(pagina=nombre, zoom=zoom, **dimensiones))
    finally:
        contexto.close()
        (salida/"mediciones.json").write_text(json.dumps(resultados, indent=2), encoding="utf-8")
print("ZOOM", json.dumps(resultados))
assert len(resultados) == 4 and all(x["contenido"] <= x["vista"]+1 for x in resultados)
