from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("registro/", views.registro, name="registro"),
    path("ingresar/", LoginView.as_view(template_name="empleo/ingresar.html", redirect_authenticated_user=True), name="login"),
    path("salir/", LogoutView.as_view(next_page="inicio"), name="logout"),
    path("panel/", views.panel, name="panel"),
    path("mi-perfil/", views.perfil_postulante, name="perfil_postulante"),
    path("empresa/perfil/", views.perfil_empresa, name="perfil_empresa"),
    path("empresa/ofertas/", views.mis_ofertas, name="mis_ofertas"),
    path("empresa/ofertas/nueva/", views.crear_oferta, name="crear_oferta"),
    path("empresa/ofertas/<int:pk>/editar/", views.editar_oferta, name="editar_oferta"),
    path("empresa/ofertas/<int:pk>/cerrar/", views.cerrar_oferta, name="cerrar_oferta"),
    path("empresa/ofertas/<int:pk>/candidatos/", views.candidatos, name="candidatos"),
    path("ofertas/", views.ofertas, name="ofertas"),
    path("ofertas/<int:pk>/", views.detalle_oferta, name="detalle_oferta"),
    path("ofertas/<int:pk>/postular/", views.postular, name="postular"),
    path("mi-cv/", views.cargar_cv, name="cargar_cv"),
    path("cv/<int:pk>/descargar/", views.descargar_cv, name="descargar_cv"),
    path("mis-postulaciones/", views.mis_postulaciones, name="mis_postulaciones"),
]
