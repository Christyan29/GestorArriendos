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
     # Dashboard admijistradror
    path('dashboard/administrador/', views.dashboard_admin, name='dashboard_admin'),
    path('contratos/crear/', views.crear_contrato, name='crear_contrato'),
    path('contratos/<int:contrato_id>/', views.detalle_contrato, name='detalle_contrato'),
    path('contratos/<int:contrato_id>/editar/', views.editar_contrato, name='editar_contrato'),
    path('contratos/<int:contrato_id>/eliminar/', views.eliminar_contrato, name='eliminar_contrato'),
    path('pagos/registrar/<int:pago_id>/', views.registrar_pago, name='registrar_pago'),
    path('pagos/vencido/<int:pago_id>/', views.marcar_vencido, name='marcar_vencido'),


    # Dashboard Arrendatario
    path('dashboard/arrendatario/', views.dashboard_arrendatario, name='dashboard_arrendatario'),
    path('dashboard/arrendatario/contratos/', views.contratos_arrendatario, name='contratos_arrendatario'),
    path('dashboard/arrendatario/notificaciones/', views.notificaciones_arrendatario, name='notificaciones_arrendatario'),
    path('dashboard/arrendatario/editar-perfil/', views.editar_perfil_arrendatario, name='editar_perfil_arrendatario'),
    path('contrato/<int:contrato_id>/pdf/', views.contrato_pdf, name='contrato_pdf'),


    path('logout/', views.cerrar_sesion, name='logout'),
    path('usuarios/', views.usuarios_admin, name='usuarios_admin'),
    path('contratos/', views.contratos_admin, name='contratos_admin'),
    path('contratos/crear/', views.crear_contrato, name='crear_contrato'),
    path('reportes/', views.reportes_admin, name='reportes_admin'),
    path('arrendatarios/', lista_arrendatarios, name='lista_arrendatarios'),


    path('pagos/', views.pagos_admin, name='pagos_admin'),
    path('notificaciones/', views.notificaciones_admin, name='notificaciones_admin'),
    path('notificacion/reintentar/<int:id>/', views.reintentar_notificacion, name='reintentar_notificacion'),
    path('notificacion/leida/<int:id>/', views.marcar_leida, name='marcar_leida'),
    path('notificacion/programar/', views.programar_manual, name='programar_manual'),

    path('exportar/pagos/', views.exportar_pagos_excel, name='exportar_pagos_excel'),
    path("tarea-avanzada/", views.ejecutar_tarea_avanzada, name="tarea_avanzada"),


]

