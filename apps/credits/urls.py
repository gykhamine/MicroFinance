from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_credits, name='liste_credits'),
    path('demande/', views.soumettre_demande, name='soumettre_demande'),
    path('<int:pk>/', views.detail_credit, name='detail_credit'),
    path('<int:pk>/instruire/', views.instruire_credit, name='instruire_credit'),
    path('<int:pk>/decaisser/', views.decaisser_credit, name='decaisser_credit'),
    path('<int:pk>/amortissement/', views.tableau_amortissement, name='tableau_amortissement'),
    path('echeance/<int:pk>/rembourser/', views.rembourser_echeance_view, name='rembourser_echeance'),
    path('types/', views.gestion_types_credit, name='types_credit'),
]
