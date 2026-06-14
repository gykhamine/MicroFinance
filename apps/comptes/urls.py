from django.urls import path
from . import views
urlpatterns = [
    path('ouvrir/', views.ouvrir_compte, name='ouvrir_compte'),
    path('<int:pk>/', views.detail_compte, name='detail_compte'),
    path('types/', views.gestion_types_comptes, name='types_comptes'),
]
