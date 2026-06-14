from django.contrib.auth.models import AbstractUser
from django.db import models

ROLE_CHOICES = [
    ('directeur', 'Directeur'),
    ('banque', 'Agent Bancaire'),
    ('caissier', 'Caissier(e)'),
    ('preteur', 'Agent de Crédit'),
    ('client', 'Client'),
]

class Utilisateur(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_staff_member(self):
        return self.role in ['directeur','banque','caissier','preteur']

    def get_role_icon(self):
        return {'directeur':'👑','banque':'🏦','caissier':'💵','preteur':'📋','client':'👤'}.get(self.role,'👤')

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'Utilisateur'
