from django.urls import path
from . import views
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard),
    path('utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('utilisateurs/creer/', views.creer_utilisateur, name='creer_utilisateur'),
    path('profil/', views.mon_profil, name='mon_profil'),
    path('notifications/', views.notifications_view, name='liste_notifications'),
    path('api/notifs/count/', views.count_notifs, name='count_notifs'),
]
