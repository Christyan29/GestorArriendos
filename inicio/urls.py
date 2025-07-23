from django.urls import path
from . import views

urlpatterns = [
    path('', views.bienvenida, name='bienvenida'),
    path('login/', views.vista_login, name='login'),
    path('nosotros/', views.vista_nosotros, name='nosotros'),
    path('contacto/', views.vista_contacto, name='contacto'),
    path('registrarse/', views.vista_registrarse, name='registrarse'),
    path('dashboard/', views.dashboard_admin, name='dashboard_admin')
]

