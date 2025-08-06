from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.bienvenida, name='bienvenida'),
    path('login/', views.vista_login, name='login'),
    path('nosotros/', views.vista_nosotros, name='nosotros'),
    path('contacto/', views.vista_contacto, name='contacto'),
    path('registrarse/', views.vista_registrarse, name='registrarse'),

    # Dashboard arrendatario
    path('dashboard/', views.dashboard_arrendatarios, name='dashboard_arrendatarios'),
    path('dashboard/contrato/', views.ver_contrato, name='contrato'),
    path('dashboard/pago/', views.vista_pago, name='pago'),
    path('dashboard/notificaciones/', views.vista_notificaciones, name='notificaciones'),
]

# Archivos multimedia
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)