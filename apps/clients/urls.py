from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_clients, name='liste_clients'),
    path('nouveau/', views.creer_client, name='creer_client'),
    path('<int:pk>/', views.detail_client, name='detail_client'),
]
