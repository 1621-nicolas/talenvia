# Migración inicial de Talenvía: usuarios, roles, ofertas, apoyos y CV privados.
import django.db.models.deletion
import django.utils.timezone
import django.core.validators
import empleo.models
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [("auth", "0012_alter_user_first_name_max_length")]

    operations = [
        migrations.CreateModel(
            name="Usuario",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="correo electrónico")),
                ("rol", models.CharField(choices=[("POSTULANTE", "Postulante"), ("EMPRESA", "Empresa"), ("ADMINISTRADOR", "Administrador")], max_length=16)),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"abstract": False},
            managers=[("objects", empleo.models.UsuarioManager())],
        ),
        migrations.CreateModel(
            name="Apoyo",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("nombre", models.CharField(max_length=120, unique=True)),
                ("descripcion", models.TextField()),
                ("activo", models.BooleanField(default=True)),
            ],
            options={"ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="Postulante",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("nombres", models.CharField(blank=True, max_length=180)),
                ("ubicacion", models.CharField(blank=True, max_length=160)),
                ("telefono", models.CharField(blank=True, max_length=30)),
                ("formacion", models.TextField(blank=True)),
                ("experiencia", models.TextField(blank=True)),
                ("habilidades", models.TextField(blank=True)),
                ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="perfil_postulante", to="empleo.usuario")),
                ("apoyos_preferidos", models.ManyToManyField(blank=True, related_name="postulantes", to="empleo.apoyo")),
            ],
        ),
        migrations.CreateModel(
            name="Empresa",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("razon_social", models.CharField(blank=True, max_length=180)),
                ("ruc", models.CharField(blank=True, max_length=11, validators=[django.core.validators.RegexValidator("^\\d{11}$", "El RUC debe tener 11 dígitos.")])),
                ("ubicacion", models.CharField(blank=True, max_length=160)),
                ("correo_contacto", models.EmailField(blank=True, max_length=254)),
                ("estado", models.CharField(choices=[("PENDIENTE", "Pendiente"), ("APROBADA", "Aprobada"), ("SUSPENDIDA", "Suspendida")], default="PENDIENTE", max_length=12)),
                ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="perfil_empresa", to="empleo.usuario")),
            ],
        ),
        migrations.CreateModel(
            name="OfertaLaboral",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("titulo", models.CharField(max_length=160)),
                ("descripcion", models.TextField()),
                ("requisitos", models.TextField()),
                ("ubicacion", models.CharField(max_length=160)),
                ("modalidad", models.CharField(choices=[("PRESENCIAL", "Presencial"), ("REMOTO", "Remoto"), ("HIBRIDO", "Híbrido")], max_length=12)),
                ("fecha_cierre", models.DateField()),
                ("publicada_en", models.DateTimeField(default=django.utils.timezone.now)),
                ("estado", models.CharField(choices=[("PUBLICADA", "Publicada"), ("CERRADA", "Cerrada")], default="PUBLICADA", max_length=10)),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ofertas", to="empleo.empresa")),
                ("apoyos", models.ManyToManyField(related_name="ofertas", to="empleo.apoyo")),
            ],
            options={"ordering": ["-publicada_en"]},
        ),
        migrations.CreateModel(
            name="Curriculum",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("archivo", models.FileField(upload_to=empleo.models.ruta_cv_privada)),
                ("tamano_bytes", models.PositiveIntegerField()),
                ("es_actual", models.BooleanField(default=True)),
                ("creado_en", models.DateTimeField(default=django.utils.timezone.now)),
                ("postulante", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="curriculums", to="empleo.postulante")),
            ],
            options={"ordering": ["-creado_en"]},
        ),
        migrations.CreateModel(
            name="Postulacion",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("fecha", models.DateTimeField(default=django.utils.timezone.now)),
                ("consentimiento", models.BooleanField(default=True)),
                ("correo_contacto", models.EmailField(max_length=254)),
                ("telefono_contacto", models.CharField(blank=True, max_length=30)),
                ("curriculum", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="postulaciones", to="empleo.curriculum")),
                ("oferta", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="postulaciones", to="empleo.ofertalaboral")),
                ("postulante", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="postulaciones", to="empleo.postulante")),
            ],
            options={"ordering": ["-fecha"]},
        ),
        migrations.AddConstraint(
            model_name="curriculum",
            constraint=models.UniqueConstraint(condition=models.Q(("es_actual", True)), fields=("postulante",), name="unico_cv_actual_por_postulante"),
        ),
        migrations.AddConstraint(
            model_name="postulacion",
            constraint=models.UniqueConstraint(fields=("postulante", "oferta"), name="unica_postulacion_por_oferta"),
        ),
    ]
