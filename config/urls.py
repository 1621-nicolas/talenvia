from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("administracion/", admin.site.urls),
    path("", include("empleo.urls")),
]
admin.site.site_header = "Talenvía · Administración"
admin.site.site_title = "Talenvía"
