"""
Rutas de la API del compilador (todas empiezan con /api/):

    GET  /api/                       estado del servidor
    POST /api/compilar               compila y ejecuta el código
    GET  /api/reporte/errores        último reporte de errores (HTML)
    GET  /api/reporte/tabla          último reporte de tabla de símbolos (HTML)
    GET  /api/reporte/ast            última imagen del AST (SVG)
    GET  /api/reporte/ast.dot        último archivo DOT del AST
"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.estado, name='estado'),
    path('compilar', views.compilar_codigo, name='compilar'),
    path('reporte/<str:nombre>', views.reporte, name='reporte'),
]
