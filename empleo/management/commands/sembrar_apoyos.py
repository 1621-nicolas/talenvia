"""Catálogo inicial de apoyos; no introduce usuarios ni datos personales."""
from django.core.management.base import BaseCommand
from empleo.models import Apoyo

APOYOS = {
    "Acceso sin escalones": "El ingreso y las áreas de trabajo permiten el acceso sin escalones.",
    "Servicios higiénicos accesibles": "Existen servicios higiénicos adaptados y accesibles.",
    "Comunicación escrita": "La empresa ofrece instrucciones y comunicación por escrito.",
    "Instrucciones paso a paso": "Las actividades pueden explicarse en pasos claros y ordenados.",
}

class Command(BaseCommand):
    help = "Crea o actualiza el catálogo inicial de apoyos del proyecto ODS 10."

    def handle(self, *args, **options):
        for nombre, descripcion in APOYOS.items():
            Apoyo.objects.update_or_create(nombre=nombre, defaults={"descripcion": descripcion, "activo": True})
        self.stdout.write(self.style.SUCCESS(f"Catálogo listo: {len(APOYOS)} apoyos."))
