"""El administrador modera empresas, ofertas y catálogo; no recibe acceso ordinario a CV."""
from django import forms
from django.contrib import admin, messages
from django.utils import timezone
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import Apoyo, Empresa, OfertaLaboral, Postulante, Usuario
from .services import registrar_perfil


class AdminUsuarioCrearForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ("email", "rol")


class AdminUsuarioCambiarForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = "__all__"


@admin.register(Usuario)
class AdminUsuario(UserAdmin):
    form = AdminUsuarioCambiarForm
    add_form = AdminUsuarioCrearForm
    list_display = ("email", "rol", "is_active", "is_staff")
    list_filter = ("rol", "is_active", "is_staff")
    ordering = ("email",)
    search_fields = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos y permisos", {"fields": ("rol", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "rol", "password1", "password2", "is_active", "is_staff", "is_superuser")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and obj.rol != Usuario.Rol.ADMINISTRADOR:
            registrar_perfil(obj)


@admin.register(Apoyo)
class AdminApoyo(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Empresa)
class AdminEmpresa(admin.ModelAdmin):
    list_display = ("razon_social", "ruc", "estado", "usuario")
    list_filter = ("estado",)
    search_fields = ("razon_social", "ruc", "usuario__email")
    readonly_fields = ("usuario",)
    actions = ("aprobar", "suspender")

    @admin.action(description="Aprobar empresas con datos completos")
    def aprobar(self, request, queryset):
        total = 0
        for empresa in queryset.select_related("usuario"):
            if empresa.completo and empresa.usuario.is_active:
                empresa.estado = Empresa.Estado.APROBADA
                empresa.save(update_fields=["estado"])
                total += 1
        self.message_user(request, f"Se aprobaron {total} empresas.", level=messages.SUCCESS)

    @admin.action(description="Suspender empresas")
    def suspender(self, request, queryset):
        total = queryset.update(estado=Empresa.Estado.SUSPENDIDA)
        self.message_user(request, f"Se suspendieron {total} empresas.", level=messages.WARNING)


class AdminOfertaForm(forms.ModelForm):
    """Al crear ofertas manuales, aplicar las mismas reglas del portal inclusivo."""

    class Meta:
        model = OfertaLaboral
        fields = "__all__"

    def clean(self):
        datos = super().clean()
        empresa = datos.get("empresa")
        if empresa is None and self.instance.pk:
            empresa = self.instance.empresa
        if empresa is not None and not empresa.habilitada:
            self.add_error("empresa" if "empresa" in self.fields else None, "La empresa debe estar aprobada, activa y con su perfil completo.")
        fecha = datos.get("fecha_cierre")
        if fecha is not None and fecha < timezone.localdate():
            self.add_error("fecha_cierre", "La fecha de cierre no puede ser anterior a hoy.")
        if self.instance.pk and (self.instance.postulaciones.exists() or self.instance.estado == OfertaLaboral.Estado.CERRADA):
            raise forms.ValidationError("No se pueden modificar las condiciones de una oferta cerrada o que ya recibió postulaciones.")
        return datos


@admin.register(OfertaLaboral)
class AdminOferta(admin.ModelAdmin):
    list_display = ("titulo", "empresa", "modalidad", "fecha_cierre", "estado")
    list_filter = ("estado", "modalidad")
    search_fields = ("titulo", "empresa__razon_social")
    form = AdminOfertaForm
    list_select_related = ("empresa",)
    filter_horizontal = ("apoyos",)
    actions = ("cerrar",)
    fields = ("empresa", "titulo", "descripcion", "requisitos", "ubicacion", "modalidad", "fecha_cierre", "apoyos", "estado", "publicada_en")

    def get_readonly_fields(self, request, obj=None):
        if obj and (obj.estado == OfertaLaboral.Estado.CERRADA or obj.postulaciones.exists()):
            return self.fields
        if obj:
            return ("empresa", "publicada_en")
        return ("publicada_en",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "empresa":
            kwargs["queryset"] = Empresa.objects.filter(
                estado=Empresa.Estado.APROBADA, usuario__is_active=True,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.action(description="Cerrar ofertas seleccionadas")
    def cerrar(self, request, queryset):
        numero = queryset.update(estado=OfertaLaboral.Estado.CERRADA)
        self.message_user(request, f"Ofertas cerradas: {numero}.", level=messages.SUCCESS)
