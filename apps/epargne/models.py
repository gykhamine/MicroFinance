from django.db import models
from apps.clients.models import Client
from apps.comptes.models import Compte
from apps.accounts.models import Utilisateur

class PlanEpargne(models.Model):
    """Plan d'épargne programmée"""
    FREQUENCE = [('quotidien','Quotidien'),('hebdomadaire','Hebdomadaire'),('mensuel','Mensuel')]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='plans_epargne')
    compte = models.ForeignKey(Compte, on_delete=models.PROTECT)
    nom = models.CharField(max_length=100)
    objectif = models.DecimalField(max_digits=12, decimal_places=2)
    montant_verse = models.DecimalField(max_digits=12, decimal_places=2)
    frequence = models.CharField(max_length=15, choices=FREQUENCE, default='mensuel')
    date_debut = models.DateField()
    date_fin_prevue = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    agent = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def progression_pct(self):
        if self.objectif == 0: return 0
        total = sum(v.montant for v in self.versements.all())
        return min(round(float(total) / float(self.objectif) * 100), 100)

    def total_verse(self):
        return sum(v.montant for v in self.versements.all())

    def __str__(self):
        return f"Plan {self.nom} — {self.client}"

class VersementEpargne(models.Model):
    plan = models.ForeignKey(PlanEpargne, on_delete=models.CASCADE, related_name='versements')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    caissier = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']
