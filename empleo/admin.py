"""El administrador modera empresas, ofertas y catálogo; no recibe acceso ordinario a CV."""
from django.contrib import admin, messages
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


@admin.register(OfertaLaboral)
class AdminOferta(admin.ModelAdmin):
    list_display = ("titulo", "empresa", "modalidad", "fecha_cierre", "estado")
    list_filter = ("estado", "modalidad")
    search_fields = ("titulo", "empresa__razon_social")
    readonly_fields = ("empresa", "titulo", "descripcion", "requisitos", "ubicacion", "modalidad", "fecha_cierre", "publicada_en", "estado", "apoyos")
    actions = ("cerrar",)

    @admin.action(description="Cerrar ofertas seleccionadas")
    def cerrar(self, request, queryset):
        numero = queryset.update(estado=OfertaLaboral.Estado.CERRADA)
        self.message_user(request, f"Ofertas cerradas: {numero}.", level=messages.SUCCESS)
