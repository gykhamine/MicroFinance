from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('clients/', include('apps.clients.urls')),
    path('comptes/', include('apps.comptes.urls')),
    path('transactions/', include('apps.transactions.urls')),
    path('cartes/', include('apps.cartes_31.urls')),
    path('credits/', include('apps.credits.urls')),
    path('epargne/', include('apps.epargne.urls')),
    path('rapports/', include('apps.rapports.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
