"""Datos para el criterio documentado de 100 ofertas en la base efímera del job k6."""
import os
from datetime import timedelta

from django.db import connection, transaction
from django.utils import timezone
from empleo.models import Empresa, OfertaLaboral

if os.getenv("GITHUB_ACTIONS") != "true" or connection.vendor != "sqlite":
    raise RuntimeError("Este generador se ejecuta en el job CI con SQLite efímero")

with transaction.atomic():
    empresas = Empresa.objects.filter(estado=Empresa.Estado.APROBADA)
    empresa = empresas.first()
    if not empresa:
        raise RuntimeError("Falta la empresa creada por sembrar_demo")
    cantidad = OfertaLaboral.disponibles().count()
    for i in range(cantidad, 100):
        OfertaLaboral.objects.create(
            empresa=empresa, titulo=f"Analista QA {i:03d}", descripcion="Datos de ensayo",
            requisitos="Análisis", ubicacion="Trujillo", modalidad="REMOTO",
            fecha_cierre=timezone.localdate()+timedelta(days=10))
    assert OfertaLaboral.disponibles().count() == 100
    print("CATALOGO 100 ofertas disponibles")
