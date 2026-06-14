from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_cartes, name='liste_cartes'),
    path('creer/', views.creer_carte, name='creer_carte'),
    path('<int:pk>/', views.detail_carte, name='detail_carte'),
    path('<int:pk>/deposer/', views.deposer_case, name='deposer_case'),
    path('<int:pk>/cloturer/', views.cloturer_carte, name='cloturer_carte'),
]
