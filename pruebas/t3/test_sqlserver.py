"""Ejecutar explícitamente con manage.py test pruebas.t3.test_sqlserver en SQL Server QA."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase
from django.utils import timezone

from empleo.models import Curriculum, Empresa, OfertaLaboral, Postulacion, Postulante, Usuario
from empleo.services import enviar_postulacion


class ConcurrenciaSQLServer(TransactionTestCase):
    def test_dos_envios_concurrentes_una_postulacion(self):
        self.assertEqual(connection.settings_dict["ENGINE"], "mssql", "Se requiere SQL Server QA")
        persona = Usuario.objects.create_user(email="conc@example.test", rol=Usuario.Rol.POSTULANTE)
        perfil = Postulante.objects.create(usuario=persona, nombres="QA", ubicacion="Trujillo")
        cuenta = Usuario.objects.create_user(email="titular@example.test", rol=Usuario.Rol.EMPRESA)
        empresa = Empresa.objects.create(usuario=cuenta, razon_social="QA", ruc="20444444444",
                                        ubicacion="Trujillo", correo_contacto=cuenta.email, estado=Empresa.Estado.APROBADA)
        oferta = OfertaLaboral.objects.create(empresa=empresa, titulo="QA", descripcion="QA",
                                             requisitos="QA", ubicacion="Trujillo", modalidad="REMOTO",
                                             fecha_cierre=timezone.localdate()+timedelta(days=2))
        Curriculum.objects.create(postulante=perfil, archivo="cv/qa.pdf", tamano_bytes=12, es_actual=True)
        inicio = Barrier(2, timeout=15)

        def enviar():
            close_old_connections()
            try:
                p = Postulante.objects.get(pk=perfil.pk)
                o = OfertaLaboral.objects.get(pk=oferta.pk)
                inicio.wait()
                try:
                    enviar_postulacion(p, o, consentimiento=True)
                    return "creada"
                except ValidationError as error:
                    if not any("postul" in msg and ("Ya " in msg) for msg in error.messages):
                        raise
                    return "duplicada"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            solicitudes = [pool.submit(enviar) for _ in range(2)]
            resultados = sorted(tarea.result(timeout=45) for tarea in solicitudes)
        self.assertEqual(resultados, ["creada", "duplicada"])
        self.assertEqual(Postulacion.objects.filter(postulante=perfil, oferta=oferta).count(), 1)
