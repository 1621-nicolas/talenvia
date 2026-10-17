"""Modelo de negocio de Talenvía (Práctica de Campo 02)."""
import uuid
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        email = self.normalize_email(email.strip()).casefold()
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("rol", "ADMINISTRADOR")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields["rol"] != "ADMINISTRADOR" or not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("El superusuario debe ser administrador y staff.")
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        POSTULANTE = "POSTULANTE", "Postulante"
        EMPRESA = "EMPRESA", "Empresa"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    username = None
    email = models.EmailField("correo electrónico", unique=True)
    rol = models.CharField(max_length=16, choices=Rol.choices)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UsuarioManager()

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().casefold()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class Apoyo(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Postulante(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.PROTECT, related_name="perfil_postulante")
    nombres = models.CharField(max_length=180, blank=True)
    ubicacion = models.CharField(max_length=160, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    formacion = models.TextField(blank=True)
    experiencia = models.TextField(blank=True)
    habilidades = models.TextField(blank=True)
    apoyos_preferidos = models.ManyToManyField(Apoyo, blank=True, related_name="postulantes")

    @property
    def completo(self):
        return bool(self.nombres.strip() and self.ubicacion.strip())

    def __str__(self):
        return self.nombres or self.usuario.email


class Empresa(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADA = "APROBADA", "Aprobada"
        SUSPENDIDA = "SUSPENDIDA", "Suspendida"

    usuario = models.OneToOneField(Usuario, on_delete=models.PROTECT, related_name="perfil_empresa")
    razon_social = models.CharField(max_length=180, blank=True)
    ruc = models.CharField(max_length=11, blank=True, validators=[RegexValidator(r"^\d{11}$", "El RUC debe tener 11 dígitos.")])
    ubicacion = models.CharField(max_length=160, blank=True)
    correo_contacto = models.EmailField(blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)

    @property
    def completo(self):
        return bool(self.razon_social.strip() and self.ruc.isdigit() and len(self.ruc) == 11 and self.ubicacion.strip() and self.correo_contacto.strip())

    @property
    def habilitada(self):
        return self.estado == self.Estado.APROBADA and self.usuario.is_active and self.completo

    def __str__(self):
        return self.razon_social or self.usuario.email


class OfertaLaboral(models.Model):
    class Modalidad(models.TextChoices):
        PRESENCIAL = "PRESENCIAL", "Presencial"
        REMOTO = "REMOTO", "Remoto"
        HIBRIDO = "HIBRIDO", "Híbrido"

    class Estado(models.TextChoices):
        PUBLICADA = "PUBLICADA", "Publicada"
        CERRADA = "CERRADA", "Cerrada"

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="ofertas")
    titulo = models.CharField(max_length=160)
    descripcion = models.TextField()
    requisitos = models.TextField()
    ubicacion = models.CharField(max_length=160)
    modalidad = models.CharField(max_length=12, choices=Modalidad.choices)
    fecha_cierre = models.DateField()
    publicada_en = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PUBLICADA)
    apoyos = models.ManyToManyField(Apoyo, related_name="ofertas")

    class Meta:
        ordering = ["-publicada_en"]

    @classmethod
    def disponibles(cls):
        return cls.objects.filter(
            estado=cls.Estado.PUBLICADA,
            fecha_cierre__gte=timezone.localdate(),
            empresa__estado=Empresa.Estado.APROBADA,
            empresa__usuario__is_active=True,
        ).select_related("empresa").prefetch_related("apoyos")

    @property
    def disponible(self):
        return (self.estado == self.Estado.PUBLICADA and self.fecha_cierre >= timezone.localdate() and self.empresa.habilitada)

    def __str__(self):
        return self.titulo


def ruta_cv_privada(instance, _filename):
    return f"cv/{instance.postulante_id}/{uuid.uuid4().hex}.pdf"


class Curriculum(models.Model):
    postulante = models.ForeignKey(Postulante, on_delete=models.PROTECT, related_name="curriculums")
    archivo = models.FileField(upload_to=ruta_cv_privada)
    tamano_bytes = models.PositiveIntegerField()
    es_actual = models.BooleanField(default=True)
    creado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-creado_en"]
        constraints = [
            models.UniqueConstraint(fields=["postulante"], condition=Q(es_actual=True), name="unico_cv_actual_por_postulante"),
        ]

    def __str__(self):
        return f"CV {self.pk} · {self.postulante}"


class Postulacion(models.Model):
    postulante = models.ForeignKey(Postulante, on_delete=models.PROTECT, related_name="postulaciones")
    oferta = models.ForeignKey(OfertaLaboral, on_delete=models.PROTECT, related_name="postulaciones")
    curriculum = models.ForeignKey(Curriculum, on_delete=models.PROTECT, related_name="postulaciones")
    fecha = models.DateTimeField(default=timezone.now)
    consentimiento = models.BooleanField(default=True)
    correo_contacto = models.EmailField()
    telefono_contacto = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["-fecha"]
        constraints = [
            models.UniqueConstraint(fields=["postulante", "oferta"], name="unica_postulacion_por_oferta"),
        ]

    def __str__(self):
        return f"{self.postulante} → {self.oferta}"
