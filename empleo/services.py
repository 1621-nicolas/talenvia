"""Operaciones de negocio y reglas de seguridad comprobables mediante pruebas."""
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from .models import Curriculum, Empresa, Postulacion


def registrar_perfil(usuario):
    """Crea el perfil asociado al rol público; el admin se crea internamente."""
    if usuario.rol == usuario.Rol.POSTULANTE:
        from .models import Postulante
        return Postulante.objects.create(usuario=usuario)
    if usuario.rol == usuario.Rol.EMPRESA:
        return Empresa.objects.create(usuario=usuario)
    raise ValidationError("No se admite registro público de administradores.")


def enviar_postulacion(postulante, oferta, *, consentimiento):
    if not consentimiento:
        raise ValidationError("Debes autorizar el envío de tus datos.")
    if not postulante.completo:
        raise ValidationError("Primero completa nombres y ubicación de tu perfil.")
    cv = Curriculum.objects.filter(postulante=postulante, es_actual=True).first()
    if cv is None:
        raise ValidationError("Debes cargar un CV en PDF.")
    try:
        with transaction.atomic():
            # Restricción única en BD como garantía ante envíos simultáneos.
            from .models import OfertaLaboral
            oferta_actual = OfertaLaboral.objects.select_for_update().select_related("empresa__usuario").get(pk=oferta.pk)
            if not oferta_actual.disponible:
                raise ValidationError("La oferta está cerrada, vencida o no disponible.")
            if Postulacion.objects.filter(postulante=postulante, oferta=oferta_actual).exists():
                raise ValidationError("Ya te postulaste a esta oferta.")
            return Postulacion.objects.create(
                postulante=postulante, oferta=oferta_actual, curriculum=cv,
                consentimiento=True, correo_contacto=postulante.usuario.email,
                telefono_contacto=postulante.telefono,
            )
    except IntegrityError as exc:
        raise ValidationError("Ya existe una postulación para esta oferta.") from exc


def puede_descargar_cv(usuario, cv):
    if not usuario.is_authenticated or not usuario.is_active:
        return False
    if usuario.rol == usuario.Rol.POSTULANTE:
        return cv.postulante.usuario_id == usuario.pk
    if usuario.rol == usuario.Rol.EMPRESA:
        return (
            Empresa.objects.filter(usuario=usuario, estado=Empresa.Estado.APROBADA).exists()
            and Postulacion.objects.filter(curriculum=cv, oferta__empresa__usuario=usuario).exists()
        )
    return False
