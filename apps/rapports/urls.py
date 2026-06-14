from django.urls import path
from . import views
urlpatterns = [
    path('', views.tableau_bord, name='rapports'),
    path('credits/', views.rapport_credits, name='rapport_credits'),
    path('cartes/', views.rapport_cartes, name='rapport_cartes'),
    path('pdf/<str:type_r>/', views.exporter_pdf, name='exporter_pdf'),
]
