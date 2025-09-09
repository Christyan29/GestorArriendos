from django.urls import path
from django.contrib.auth import views as auth_views
from inicio.forms import CustomPasswordResetForm, CustomSetPasswordForm

from .views.publicas import bienvenida, vista_nosotros, vista_contacto
from .views.autenticacion import vista_login, cerrar_sesion, admin_logout_redirect
from .views.admin import (
    dashboard_admin, lista_arrendatarios, usuarios_admin, reportes_admin,
    contratos_admin, crear_contrato, detalle_contrato, editar_contrato, eliminar_contrato,
    pagos_admin, registrar_pago, marcar_vencido, exportar_pagos_excel,
    validar_comprobante, rechazar_comprobante, notificaciones_admin, reintentar_notificacion, marcar_leida, programar_manual,
    ejecutar_tarea_avanzada, subir_comprobante_admin, historial_validaciones ,lista_arrendatarios,
    activar_arrendatario,desactivar_arrendatario,crear_arrendatario, editar_arrendatario
)
from .views.arrendatario import (
    dashboard_arrendatario, contratos_arrendatario, notificaciones_arrendatario,
    editar_perfil_arrendatario, contrato_pdf, subir_comprobante_arrendatario, pagos_arrendatario
)

urlpatterns = [
    # --- recupera  contraseña ---
    path('password-reset/', auth_views.PasswordResetView.as_view(
        form_class=CustomPasswordResetForm,
        template_name='registration/password_reset_form.html'
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        form_class=CustomSetPasswordForm,
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # --- publicas ---
    path('', bienvenida, name='bienvenida'),
    path('nosotros/', vista_nosotros, name='nosotros'),
    path('contacto/', vista_contacto, name='contacto'),

    # --- autenticacion ---
    path('login/', vista_login, name='login'),
    path('accounts/login/', vista_login, name='login'),
    path('logout/', cerrar_sesion, name='logout'),
    path('logout/admin/', admin_logout_redirect, name='admin_logout_redirect'),


    # --- admin edificio ---
    path('arrendatarios/', lista_arrendatarios, name='lista_arrendatarios'),
    path('arrendatarios/crear/', crear_arrendatario, name='crear_arrendatario'),
    path('arrendatarios/<int:user_id>/editar/', editar_arrendatario, name='editar_arrendatario'),

    path('arrendatarios/<int:user_id>/activar/', activar_arrendatario, name='activar_arrendatario'),
    path('arrendatarios/<int:user_id>/desactivar/', desactivar_arrendatario, name='desactivar_arrendatario'),
    path('dashboard/administrador/', dashboard_admin, name='dashboard_admin'),
    path('historial/validaciones/', historial_validaciones, name='historial_validaciones'),


    # contratosadmin
    path('contratos/', contratos_admin, name='contratos_admin'),
    path('contratos/crear/', crear_contrato, name='crear_contrato'),
    path('contratos/<int:contrato_id>/', detalle_contrato, name='detalle_contrato'),
    path('contratos/<int:contrato_id>/editar/', editar_contrato, name='editar_contrato'),
    path('contratos/<int:contrato_id>/eliminar/', eliminar_contrato, name='eliminar_contrato'),

    # pagos admin
    path('pagos/', pagos_admin, name='pagos_admin'),
    path('pagos/registrar/<int:pago_id>/', registrar_pago, name='registrar_pago'),
    path('pagos/vencido/<int:pago_id>/', marcar_vencido, name='marcar_vencido'),
    path('exportar/pagos/', exportar_pagos_excel, name='exportar_pagos_excel'),


    path('pagos/<int:pago_id>/subir-comprobante/', subir_comprobante_admin, name='subir_comprobante_admin'),
    path('pagos/<int:pago_id>/validar/', validar_comprobante, name='validar_comprobante'),
    path('pagos/<int:pago_id>/rechazar/', rechazar_comprobante, name='rechazar_comprobante'),

    # notificaciones admin
    path('notificaciones/', notificaciones_admin, name='notificaciones_admin'),
    path('notificacion/reintentar/<int:id>/', reintentar_notificacion, name='reintentar_notificacion'),
    path('notificacion/leida/<int:id>/', marcar_leida, name='marcar_leida'),
    path('notificacion/programar/', programar_manual, name='programar_manual'),

    # tareas admin
    path("tarea-avanzada/", ejecutar_tarea_avanzada, name="tarea_avanzada"),

    # --- arrendatario ---
    path('dashboard/arrendatario/', dashboard_arrendatario, name='dashboard_arrendatario'),
    path('dashboard/arrendatario/contratos/', contratos_arrendatario, name='contratos_arrendatario'),
    path('dashboard/arrendatario/notificaciones/', notificaciones_arrendatario, name='notificaciones_arrendatario'),
    path('dashboard/arrendatario/editar-perfil/', editar_perfil_arrendatario, name='editar_perfil_arrendatario'),
    path('arrendatario/pagos/', pagos_arrendatario, name='pagos_arrendatario'),

    path('arrendatario/comprobante/<int:pago_id>/', subir_comprobante_arrendatario, name='subir_comprobante_arrendatario'),
    path('contrato/<int:contrato_id>/pdf/', contrato_pdf, name='contrato_pdf'),
]
