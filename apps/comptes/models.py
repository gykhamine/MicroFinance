from django.db import models
from apps.clients.models import Client
from apps.accounts.models import Utilisateur
from decimal import Decimal

class TypeCompte(models.Model):
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    solde_minimum = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    frais_ouverture = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taux_interet_annuel = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    actif = models.BooleanField(default=True)
    def __str__(self): return f"{self.code} — {self.nom}"

class Compte(models.Model):
    STATUT = [('actif','Actif'),('bloque','Bloqué'),('cloture','Clôturé')]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='comptes')
    type_compte = models.ForeignKey(TypeCompte, on_delete=models.PROTECT)
    numero = models.CharField(max_length=25, unique=True)
    solde = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=STATUT, default='actif')
    date_ouverture = models.DateField(auto_now_add=True)
    date_cloture = models.DateField(null=True, blank=True)
    agent_ouverture = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    actif = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            import random
            self.numero = f"ACC{random.randint(1000000000, 9999999999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero} — {self.client} ({self.type_compte.code})"

    class Meta:
        ordering = ['-date_ouverture']
