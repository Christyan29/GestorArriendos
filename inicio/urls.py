from inicio.forms import CustomPasswordResetForm
from inicio.forms import CustomSetPasswordForm
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from inicio.views import lista_arrendatarios
from django.urls import include
from django.contrib.auth import views as auth_views
from .views import crear_admin_view
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            form_class=CustomPasswordResetForm,
            template_name='registration/password_reset_form.html',
            success_url='/password-reset/done/'
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
    'password-reset-confirm/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(
        form_class=CustomSetPasswordForm,
        template_name='registration/password_reset_confirm.html',
        success_url='/password-reset-complete/'
    ),
    name='password_reset_confirm'
),

    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),


    path('', views.bienvenida, name='bienvenida'),
    path('admin/inicio/perfilusuario/crear-admin/', crear_admin_view, name='crear_admin'),
    path('login/', views.vista_login, name='login'),
    path('accounts/login/', views.vista_login, name='login'),
    path('nosotros/', views.vista_nosotros, name='nosotros'),
    path('contacto/', views.vista_contacto, name='contacto'),
    path('registrarse/', views.vista_registrarse, name='registrarse'),
    path('panel/', views.dashboard_admin, name='dashboard_admin'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('usuarios/', views.usuarios_admin, name='usuarios_admin'),
    path('contratos/', views.contratos_admin, name='contratos_admin'),
    path('contratos/crear/', views.crear_contrato, name='crear_contrato'),
    path('reportes/', views.reportes_admin, name='reportes_admin'),
    path('arrendatarios/', lista_arrendatarios, name='lista_arrendatarios'),
    path('admin/buscar/', views.admin_buscar, name='admin_buscar'),
    path('vencimientos/', views.vencimientos_admin, name='vencimientos_admin'),
    path('pagos/', views.pagos_admin, name='pagos_admin'),
    path('notificaciones/', views.notificaciones_admin, name='notificaciones_admin'),

    path('exportar/pagos/', views.exportar_pagos_excel, name='exportar_pagos_excel'),
    path("tarea-avanzada/", views.ejecutar_tarea_avanzada, name="tarea_avanzada"),


]

