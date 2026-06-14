from django.urls import path
from . import views
urlpatterns = [
    path('depot/', views.faire_depot, name='faire_depot'),
    path('retrait/', views.faire_retrait, name='faire_retrait'),
    path('transfert/', views.faire_transfert, name='faire_transfert'),
    path('journal/', views.journal_transactions, name='journal_transactions'),
    path('taxes/', views.gestion_taxes, name='gestion_taxes'),
    path('api/comptes/', views.get_comptes_client, name='get_comptes_client'),
]
