"""Controladores accesibles; todas las verificaciones de permisos ocurren en el servidor."""
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .forms import ConsentimientoForm, CurriculumForm, OfertaForm, PerfilEmpresaForm, PerfilPostulanteForm, RegistroForm
from .models import Apoyo, Curriculum, Empresa, OfertaLaboral, Postulacion, Usuario
from .services import enviar_postulacion, puede_descargar_cv, registrar_perfil


def requiere_rol(rol):
    def decorador(vista):
        @login_required
        @wraps(vista)
        def verificar(request, *args, **kwargs):
            if not request.user.is_active or request.user.rol != rol:
                return HttpResponseForbidden("No tienes permiso para esta operación.")
            return vista(request, *args, **kwargs)
        return verificar
    return decorador


def inicio(request):
    return render(request, "empleo/inicio.html", {"ofertas": OfertaLaboral.disponibles()[:6]})


def registro(request):
    if request.user.is_authenticated:
        return redirect("panel")
    tipo_inicial = Usuario.Rol.EMPRESA if request.GET.get("tipo") == "empresa" else Usuario.Rol.POSTULANTE
    formulario = RegistroForm(request.POST or None, initial={"rol": tipo_inicial})
    if request.method == "POST" and formulario.is_valid():
        with transaction.atomic():
            usuario = formulario.save()
            registrar_perfil(usuario)
        login(request, usuario)
        messages.success(request, "Tu cuenta fue creada. Bienvenido a Talenvía.")
        return redirect("panel")
    return render(request, "empleo/formulario.html", {"form": formulario, "titulo": "Crear una cuenta", "texto": "El registro no solicita diagnóstico ni certificado médico.", "boton": "Registrarme"})


@login_required
def panel(request):
    if not request.user.is_active:
        return HttpResponseForbidden("Cuenta inactiva.")
    if request.user.rol == Usuario.Rol.POSTULANTE:
        return render(request, "empleo/panel.html", {"tipo": "postulante", "perfil": request.user.perfil_postulante})
    if request.user.rol == Usuario.Rol.EMPRESA:
        return render(request, "empleo/panel.html", {"tipo": "empresa", "perfil": request.user.perfil_empresa})
    return redirect("/administracion/")


@requiere_rol(Usuario.Rol.POSTULANTE)
def perfil_postulante(request):
    perfil = request.user.perfil_postulante
    formulario = PerfilPostulanteForm(request.POST or None, instance=perfil)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Tu perfil se guardó correctamente.")
        return redirect("panel")
    return render(request, "empleo/formulario.html", {"form": formulario, "titulo": "Mi perfil profesional", "texto": "Las preferencias de apoyo son privadas y opcionales. No se pide información médica.", "boton": "Guardar perfil"})


@requiere_rol(Usuario.Rol.EMPRESA)
def perfil_empresa(request):
    perfil = request.user.perfil_empresa
    formulario = PerfilEmpresaForm(request.POST or None, instance=perfil)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Datos guardados. Un administrador revisará la empresa antes de habilitar publicaciones.")
        return redirect("panel")
    return render(request, "empleo/formulario.html", {"form": formulario, "titulo": "Datos de la empresa", "texto": "La aprobación es una revisión interna, no una certificación oficial.", "boton": "Guardar empresa"})


def ofertas(request):
    consulta = OfertaLaboral.disponibles()
    texto = request.GET.get("q", "").strip()
    ubicacion = request.GET.get("ubicacion", "").strip()
    modalidad = request.GET.get("modalidad", "").strip()
    apoyos = request.GET.getlist("apoyo")
    if texto:
        from django.db.models import Q
        consulta = consulta.filter(Q(titulo__icontains=texto) | Q(descripcion__icontains=texto) | Q(requisitos__icontains=texto))
    if ubicacion:
        consulta = consulta.filter(ubicacion__icontains=ubicacion)
    if modalidad in OfertaLaboral.Modalidad.values:
        consulta = consulta.filter(modalidad=modalidad)
    ids_validos = {str(pk) for pk in Apoyo.objects.filter(activo=True).values_list("pk", flat=True)}
    elegidos = set(apoyos)
    # Si se recibe un ID inexistente o desactivado, no se ignora silenciosamente.
    # Ignorarlo mostraría TODAS las ofertas y daría resultados engañosos.
    if elegidos and not elegidos.issubset(ids_validos):
        consulta = consulta.none()
    else:
        for pk in elegidos:
            consulta = consulta.filter(apoyos__pk=pk)
    pagina = Paginator(consulta.distinct(), 10).get_page(request.GET.get("pagina"))
    return render(request, "empleo/ofertas.html", {
        "pagina": pagina, "apoyos": Apoyo.objects.filter(activo=True),
        "modalidades": OfertaLaboral.Modalidad.choices, "q": texto,
        "ubicacion": ubicacion, "modalidad": modalidad, "apoyos_seleccionados": apoyos,
    })


def detalle_oferta(request, pk):
    oferta = get_object_or_404(OfertaLaboral.disponibles(), pk=pk)
    ya_postulo = False
    if request.user.is_authenticated and request.user.rol == Usuario.Rol.POSTULANTE:
        ya_postulo = Postulacion.objects.filter(oferta=oferta, postulante__usuario=request.user).exists()
    return render(request, "empleo/detalle_oferta.html", {"oferta": oferta, "ya_postulo": ya_postulo, "form": ConsentimientoForm()})


def _empresa_habilitada(request):
    perfil = request.user.perfil_empresa
    if not perfil.habilitada:
        messages.error(request, "Completa el perfil y espera la aprobación administrativa de la empresa.")
        return None
    return perfil


@requiere_rol(Usuario.Rol.EMPRESA)
def mis_ofertas(request):
    perfil = request.user.perfil_empresa
    return render(request, "empleo/mis_ofertas.html", {"ofertas": perfil.ofertas.all(), "empresa": perfil})


@requiere_rol(Usuario.Rol.EMPRESA)
def crear_oferta(request):
    empresa = _empresa_habilitada(request)
    if empresa is None:
        return redirect("perfil_empresa")
    formulario = OfertaForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        oferta = formulario.save(commit=False)
        oferta.empresa = empresa
        oferta.save()
        formulario.save_m2m()
        messages.success(request, "La oferta se publicó correctamente.")
        return redirect("mis_ofertas")
    return render(request, "empleo/formulario.html", {"form": formulario, "titulo": "Publicar una oferta accesible", "texto": "Describe los apoyos concretos y las condiciones del puesto.", "boton": "Publicar oferta"})


@requiere_rol(Usuario.Rol.EMPRESA)
def editar_oferta(request, pk):
    empresa = _empresa_habilitada(request)
    if empresa is None:
        return redirect("perfil_empresa")
    oferta = get_object_or_404(OfertaLaboral, pk=pk, empresa=empresa)
    if oferta.postulaciones.exists() or oferta.estado == OfertaLaboral.Estado.CERRADA:
        return HttpResponseForbidden("No se pueden modificar las condiciones de una oferta con postulaciones o cerrada.")
    formulario = OfertaForm(request.POST or None, instance=oferta)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Oferta actualizada.")
        return redirect("mis_ofertas")
    return render(request, "empleo/formulario.html", {"form": formulario, "titulo": "Editar oferta", "boton": "Guardar cambios"})


@require_POST
@requiere_rol(Usuario.Rol.EMPRESA)
def cerrar_oferta(request, pk):
    empresa = _empresa_habilitada(request)
    if empresa is None:
        return redirect("perfil_empresa")
    oferta = get_object_or_404(OfertaLaboral, pk=pk, empresa=empresa)
    oferta.estado = OfertaLaboral.Estado.CERRADA
    oferta.save(update_fields=["estado"])
    messages.success(request, "La oferta quedó cerrada.")
    return redirect("mis_ofertas")


@requiere_rol(Usuario.Rol.POSTULANTE)
def cargar_cv(request):
    formulario = CurriculumForm(request.POST or None, request.FILES or None)
    perfil = request.user.perfil_postulante
    if request.method == "POST" and formulario.is_valid():
        archivo = formulario.cleaned_data["archivo"]
        with transaction.atomic():
            Curriculum.objects.filter(postulante=perfil, es_actual=True).update(es_actual=False)
            cv = Curriculum.objects.create(postulante=perfil, archivo=archivo, tamano_bytes=archivo.size, es_actual=True)
        messages.success(request, f"CV cargado: versión {cv.pk}. Tus postulaciones previas no cambian.")
        return redirect("cargar_cv")
    return render(request, "empleo/cv.html", {"form": formulario, "cv_actual": Curriculum.objects.filter(postulante=perfil, es_actual=True).first()})


@login_required
def descargar_cv(request, pk):
    cv = get_object_or_404(Curriculum.objects.select_related("postulante__usuario"), pk=pk)
    if not puede_descargar_cv(request.user, cv):
        return HttpResponseForbidden("No puedes consultar este CV.")
    try:
        archivo = cv.archivo.open("rb")
    except (FileNotFoundError, OSError, ValueError):
        raise Http404("El archivo no está disponible.")
    respuesta = FileResponse(archivo, content_type="application/pdf", as_attachment=True, filename="curriculum.pdf")
    respuesta["Cache-Control"] = "private, no-store"
    return respuesta


@require_POST
@requiere_rol(Usuario.Rol.POSTULANTE)
def postular(request, pk):
    oferta = get_object_or_404(OfertaLaboral, pk=pk)
    formulario = ConsentimientoForm(request.POST)
    if not formulario.is_valid():
        messages.error(request, "Debes autorizar compartir tu CV y datos de contacto.")
        return redirect("detalle_oferta", pk=pk)
    try:
        enviar_postulacion(request.user.perfil_postulante, oferta, consentimiento=formulario.cleaned_data["acepto"])
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
        return redirect("detalle_oferta", pk=pk)
    messages.success(request, "Postulación enviada. La empresa podrá contactarte por correo o teléfono.")
    return redirect("mis_postulaciones")


@requiere_rol(Usuario.Rol.POSTULANTE)
def mis_postulaciones(request):
    items = Postulacion.objects.filter(postulante__usuario=request.user).select_related("oferta__empresa", "curriculum")
    return render(request, "empleo/mis_postulaciones.html", {"postulaciones": items})


@requiere_rol(Usuario.Rol.EMPRESA)
def candidatos(request, pk):
    empresa = _empresa_habilitada(request)
    if empresa is None:
        return redirect("perfil_empresa")
    oferta = get_object_or_404(OfertaLaboral, pk=pk, empresa=empresa)
    items = oferta.postulaciones.select_related("postulante", "curriculum")
    return render(request, "empleo/candidatos.html", {"oferta": oferta, "postulaciones": items})
