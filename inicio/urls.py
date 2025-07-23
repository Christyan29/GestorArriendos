from django.urls import path
from . import views
from inicio.views import lista_arrendatarios

urlpatterns = [
    path('', views.bienvenida, name='bienvenida'),
    path('login/', views.vista_login, name='login'),
    path('nosotros/', views.vista_nosotros, name='nosotros'),
    path('contacto/', views.vista_contacto, name='contacto'),
    path('registrarse/', views.vista_registrarse, name='registrarse'),
    path('dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('usuarios/', views.usuarios_admin, name='usuarios_admin'),
    path('contratos/', views.contratos_admin, name='contratos_admin'),
    path('reportes/', views.reportes_admin, name='reportes_admin'),
    path('arrendatarios/', lista_arrendatarios, name='lista_arrendatarios'),

]

