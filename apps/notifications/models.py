from django.db import models
from apps.accounts.models import Utilisateur

class Notification(models.Model):
    TYPE = [('info','Info'),('alerte','Alerte'),('retard','Retard crédit'),('carte','Carte 31')]
    destinataire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    expediteur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifs_envoyees')
    titre = models.CharField(max_length=200)
    message = models.TextField()
    type_notif = models.CharField(max_length=10, choices=TYPE, default='info')
    lue = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    lien = models.CharField(max_length=200, blank=True)
    class Meta:
        ordering = ['-date']

