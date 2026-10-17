"""Migración de integridad para Talenvía. No borra registros."""
from django.core.validators import RegexValidator
from django.db import migrations, models
from django.db.models import F


def verificar(apps, schema_editor):
    Postulante = apps.get_model("empleo", "Postulante")
    Empresa = apps.get_model("empleo", "Empresa")
    Postulacion = apps.get_model("empleo", "Postulacion")
    alias = schema_editor.connection.alias
    errores = []
    if Postulante.objects.using(alias).exclude(usuario__rol="POSTULANTE").exists():
        errores.append("Existen perfiles postulante asociados a otros roles")
    if Empresa.objects.using(alias).exclude(usuario__rol="EMPRESA").exists():
        errores.append("Existen perfiles empresa asociados a otros roles")
    if Postulacion.objects.using(alias).exclude(curriculum__postulante_id=F("postulante_id")).exists():
        errores.append("Existen postulaciones con CV de otra persona")
    vistos = set()
    for ruc in Empresa.objects.using(alias).values_list("ruc", flat=True):
        valor = (ruc or "").strip()
        if not valor:
            continue
        if len(valor) != 11 or not valor.isdigit():
            errores.append("Hay RUC no vacíos que no tienen 11 dígitos")
            break
        if valor in vistos:
            errores.append("Hay RUC duplicados: " + valor)
            break
        vistos.add(valor)
    if errores:
        raise RuntimeError(
            "No se aplicaron los cambios: " + "; ".join(errores)
            + ". Corrige los registros después de realizar un respaldo."
        )


def normalizar_ruc(apps, schema_editor):
    Empresa = apps.get_model("empleo", "Empresa")
    alias = schema_editor.connection.alias
    for pk, ruc in Empresa.objects.using(alias).values_list("pk", "ruc").iterator():
        corregido = (ruc or "").strip() or None
        if ruc != corregido:
            Empresa.objects.using(alias).filter(pk=pk).update(ruc=corregido)


def revertir_normalizacion(apps, schema_editor):
    Empresa = apps.get_model("empleo", "Empresa")
    Empresa.objects.using(schema_editor.connection.alias).filter(ruc__isnull=True).update(ruc="")


def identificar_historicos(apps, schema_editor):
    Postulacion = apps.get_model("empleo", "Postulacion")
    Postulacion.objects.using(schema_editor.connection.alias).filter(
        consentimiento_version=""
    ).update(consentimiento_version="historico-sin-evidencia")


class Migration(migrations.Migration):
    dependencies = [("empleo", "0001_initial")]

    operations = [
        migrations.RunPython(verificar, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="empresa", name="ruc",
            field=models.CharField(max_length=11, blank=True, null=True,
                                   validators=[RegexValidator(r"^\d{11}$", "El RUC debe tener 11 dígitos.")]),
        ),
        migrations.RunPython(normalizar_ruc, revertir_normalizacion),
        migrations.AlterField(
            model_name="empresa", name="ruc",
            field=models.CharField(max_length=11, blank=True, null=True, unique=True,
                                   validators=[RegexValidator(r"^\d{11}$", "El RUC debe tener 11 dígitos.")]),
        ),
        migrations.AddField(
            model_name="ofertalaboral", name="detalle_accesibilidad",
            field=models.TextField(blank=True, default="",
                                   help_text="Describe cómo se proporcionan los apoyos en esta vacante."),
        ),
        migrations.AddField(
            model_name="postulacion", name="consentimiento_fecha",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="postulacion", name="consentimiento_version",
            field=models.CharField(max_length=40, blank=True, default=""),
        ),
        migrations.RunPython(identificar_historicos, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="ofertalaboral",
            index=models.Index(fields=["estado", "fecha_cierre"], name="idx_oferta_estado_fecha"),
        ),
        migrations.AddIndex(
            model_name="ofertalaboral",
            index=models.Index(fields=["empresa", "estado"], name="idx_oferta_empresa_estado"),
        ),
        migrations.AddIndex(
            model_name="postulacion",
            index=models.Index(fields=["oferta", "-fecha"], name="idx_postulacion_oferta_fecha"),
        ),
    ]
