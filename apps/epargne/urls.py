from django.urls import path
from . import views
urlpatterns = [
    path('', views.liste_plans, name='liste_plans'),
    path('creer/', views.creer_plan, name='creer_plan'),
    path('<int:pk>/', views.detail_plan, name='detail_plan'),
    path('<int:pk>/verser/', views.ajouter_versement, name='ajouter_versement'),
]
