"""Formularios con validación, etiquetas e instrucciones accesibles."""
from pathlib import Path
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Usuario, Apoyo, Postulante, Empresa, OfertaLaboral

LIMITE_CV_BYTES = 5_000_000


class RegistroForm(UserCreationForm):
    rol = forms.ChoiceField(
        choices=[(Usuario.Rol.POSTULANTE, "Busco empleo"), (Usuario.Rol.EMPRESA, "Represento a una empresa")],
        label="Tipo de cuenta",
    )

    razon_social = forms.CharField(max_length=180, required=False, label="Razón social",
                                  widget=forms.TextInput(attrs={"autocomplete": "organization"}))
    ruc = forms.CharField(max_length=11, required=False, label="RUC de la empresa (11 dígitos)",
                          widget=forms.TextInput(attrs={"inputmode": "numeric", "pattern": "[0-9]{11}",
                                                        "maxlength": "11", "autocomplete": "off"}))
    ubicacion = forms.CharField(max_length=160, required=False, label="Ciudad o ubicación de la empresa")
    correo_contacto = forms.EmailField(required=False, label="Correo de contacto empresarial",
                                       widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    class Meta:
        model = Usuario
        fields = ("email", "rol")
        labels = {"email": "Correo electrónico de acceso"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(["rol", "email", "razon_social", "ruc", "ubicacion",
                           "correo_contacto", "password1", "password2"])
        self.fields["password1"].help_text = "Mínimo 12 caracteres. Evita contraseñas comunes."

    def clean_ruc(self):
        if self.data.get("rol") != Usuario.Rol.EMPRESA:
            return None
        ruc = (self.cleaned_data.get("ruc") or "").strip()
        if ruc and (len(ruc) != 11 or not ruc.isascii() or not ruc.isdigit()):
            raise ValidationError("Ingresa un RUC válido de exactamente 11 dígitos.")
        if ruc and Empresa.objects.filter(ruc=ruc).exists():
            raise ValidationError("Este RUC ya está registrado.")
        return ruc or None

    def clean(self):
        datos = super().clean()
        if datos.get("rol") == Usuario.Rol.EMPRESA:
            for campo in ("razon_social", "ruc", "ubicacion", "correo_contacto"):
                if campo not in self.errors and not datos.get(campo):
                    self.add_error(campo, "Este dato es obligatorio para registrar una empresa.")
        return datos

    def clean_email(self):
        email = self.cleaned_data["email"].strip().casefold()
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError("Este correo ya está registrado.")
        return email


class PerfilPostulanteForm(forms.ModelForm):
    class Meta:
        model = Postulante
        fields = ("nombres", "ubicacion", "telefono", "formacion", "experiencia", "habilidades", "apoyos_preferidos")
        labels = {
            "nombres": "Nombres y apellidos", "ubicacion": "Ubicación",
            "telefono": "Teléfono (opcional)", "formacion": "Formación",
            "experiencia": "Experiencia (puedes indicar Sin experiencia)",
            "habilidades": "Habilidades", "apoyos_preferidos": "Apoyos que prefieres (opcional y privado)",
        }
        widgets = {"apoyos_preferidos": forms.CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["apoyos_preferidos"].queryset = Apoyo.objects.filter(activo=True)


class PerfilEmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ("razon_social", "ruc", "ubicacion", "correo_contacto")
        labels = {"razon_social": "Razón social", "ruc": "RUC (11 dígitos)", "ubicacion": "Ubicación", "correo_contacto": "Correo de contacto"}

    def clean_ruc(self):
        valor = (self.cleaned_data.get("ruc") or "").strip()
        if valor and (len(valor) != 11 or not valor.isdigit()):
            raise ValidationError("El RUC debe contener exactamente 11 dígitos.")
        return valor or None


class OfertaForm(forms.ModelForm):
    apoyos = forms.ModelMultipleChoiceField(
        queryset=Apoyo.objects.none(), widget=forms.CheckboxSelectMultiple,
        required=True, label="Apoyos que ofrece el puesto (mínimo uno)",
    )

    class Meta:
        model = OfertaLaboral
        fields = ("titulo", "descripcion", "requisitos", "ubicacion", "modalidad", "fecha_cierre", "apoyos", "detalle_accesibilidad")
        labels = {"titulo": "Título del puesto", "descripcion": "Descripción del puesto", "detalle_accesibilidad": "Cómo se ofrecen los apoyos en este puesto (opcional)", "requisitos": "Requisitos", "ubicacion": "Ubicación", "modalidad": "Modalidad", "fecha_cierre": "Fecha de cierre"}
        widgets = {"fecha_cierre": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"), "descripcion": forms.Textarea(attrs={"rows": 4}), "requisitos": forms.Textarea(attrs={"rows": 3}), "detalle_accesibilidad": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["apoyos"].queryset = Apoyo.objects.filter(activo=True)

    def clean_fecha_cierre(self):
        fecha = self.cleaned_data["fecha_cierre"]
        if fecha < timezone.localdate():
            raise ValidationError("La fecha de cierre no puede ser anterior a hoy.")
        return fecha


class CurriculumForm(forms.Form):
    archivo = forms.FileField(label="Currículum en PDF (máximo 5 MB)")

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if not archivo.size or archivo.size > LIMITE_CV_BYTES:
            raise ValidationError("El PDF debe ocupar entre 1 y 5 000 000 de bytes.")
        if Path(archivo.name).suffix.lower() != ".pdf":
            raise ValidationError("Solo se admiten archivos PDF.")
        archivo.seek(0)
        cabecera = archivo.read(5)
        archivo.seek(max(0, archivo.size - 2048))
        cierre = archivo.read()
        archivo.seek(0)
        if cabecera != b"%PDF-" or b"%%EOF" not in cierre:
            raise ValidationError("El archivo no contiene un PDF válido.")
        return archivo


class ConsentimientoForm(forms.Form):
    acepto = forms.BooleanField(
        required=True,
        label="Autorizo compartir la versión actual de mi CV, mi correo y mi teléfono (si lo proporcioné) con esta empresa, solo para esta postulación.",
        error_messages={"required": "Debes autorizar el envío de tus datos antes de postular."},
    )
