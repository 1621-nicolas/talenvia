"""Crea datos ficticios para mostrar el diseño en desarrollo local (nunca producción)."""
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from empleo.models import Apoyo, Empresa, OfertaLaboral, Usuario


MUESTRAS = [
    {
        "correo": "demo-verdetech@talenvia.invalid", "razon_social": "DEMO VerdeTech",
        "ruc": "00000000001", "ubicacion": "Trujillo",
        "titulo": "Analista de datos junior", "modalidad": "REMOTO",
        "descripcion": "[DATOS FICTICIOS] Analiza información y colabora con equipos para mejorar procesos de una organización inclusiva.",
        "requisitos": "Conocimientos básicos de hojas de cálculo, trabajo en equipo y comunicación clara.",
        "apoyos": ["Comunicación escrita", "Instrucciones paso a paso"],
    },
    {
        "correo": "demo-conectados@talenvia.invalid", "razon_social": "DEMO Conectados",
        "ruc": "00000000002", "ubicacion": "Lima",
        "titulo": "Asistente administrativo", "modalidad": "HIBRIDO",
        "descripcion": "[DATOS FICTICIOS] Ayuda con la coordinación de actividades administrativas, documentación y comunicación.",
        "requisitos": "Organización, manejo básico de herramientas ofimáticas y disposición para aprender.",
        "apoyos": ["Acceso sin escalones", "Comunicación escrita"],
    },
    {
        "correo": "demo-crear@talenvia.invalid", "razon_social": "DEMO CreaAccesible",
        "ruc": "00000000003", "ubicacion": "Arequipa",
        "titulo": "Diseñador o diseñadora UI", "modalidad": "REMOTO",
        "descripcion": "[DATOS FICTICIOS] Participa en la creación de experiencias digitales comprensibles y accesibles.",
        "requisitos": "Fundamentos de diseño digital, tipografía, prototipos y sensibilidad por la inclusión.",
        "apoyos": ["Comunicación escrita", "Instrucciones paso a paso"],
    },
    {
        "correo": "demo-impacta@talenvia.invalid", "razon_social": "DEMO Impacta Social",
        "ruc": "00000000004", "ubicacion": "Piura",
        "titulo": "Especialista en atención al cliente", "modalidad": "PRESENCIAL",
        "descripcion": "[DATOS FICTICIOS] Orienta a usuarios con empatía y aporta soluciones a sus consultas.",
        "requisitos": "Habilidades de comunicación, organización y enfoque en la atención inclusiva.",
        "apoyos": ["Acceso sin escalones", "Servicios higiénicos accesibles"],
    },
]


class Command(BaseCommand):
    help = "Crea cuatro ofertas ficticias DEMO para la vista local; requiere --confirmar."

    def add_arguments(self, parser):
        parser.add_argument("--confirmar", action="store_true", help="Confirma que estás en un entorno local de pruebas.")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("La carga DEMO está bloqueada fuera del modo desarrollo.")
        if not options["confirmar"]:
            raise CommandError("Este comando agrega datos ficticios. Repite con --confirmar si deseas hacerlo.")
        apoyos = {
            "Acceso sin escalones": "Ingreso al puesto sin escalones.",
            "Servicios higiénicos accesibles": "Servicios sanitarios con características de accesibilidad.",
            "Comunicación escrita": "Comunicación e instrucciones disponibles por escrito.",
            "Instrucciones paso a paso": "Indicaciones divididas en pasos claros.",
        }
        for nombre, descripcion in apoyos.items():
            Apoyo.objects.get_or_create(nombre=nombre, defaults={"descripcion": descripcion})
        for item in MUESTRAS:
            usuario, _ = Usuario.objects.get_or_create(
                email=item["correo"],
                defaults={"rol": Usuario.Rol.EMPRESA, "is_active": True},
            )
            if usuario.rol != Usuario.Rol.EMPRESA:
                raise CommandError(f"El correo ficticio {item['correo']} ya corresponde a otro rol.")
            if usuario.has_usable_password():
                usuario.set_unusable_password()
                usuario.save(update_fields=["password"])
            empresa, _ = Empresa.objects.update_or_create(
                usuario=usuario,
                defaults={
                    "razon_social": item["razon_social"], "ruc": item["ruc"],
                    "ubicacion": item["ubicacion"], "correo_contacto": item["correo"],
                    "estado": Empresa.Estado.APROBADA,
                },
            )
            oferta, _ = OfertaLaboral.objects.update_or_create(
                empresa=empresa, titulo=item["titulo"],
                defaults={
                    "descripcion": item["descripcion"], "requisitos": item["requisitos"],
                    "ubicacion": item["ubicacion"], "modalidad": item["modalidad"],
                    "fecha_cierre": timezone.localdate() + timedelta(days=120),
                    "estado": OfertaLaboral.Estado.PUBLICADA,
                },
            )
            oferta.apoyos.set(Apoyo.objects.filter(nombre__in=item["apoyos"]))
        self.stdout.write(self.style.SUCCESS("Ofertas DEMO creadas/actualizadas. Son ficticias y solo para desarrollo."))
