from django.db import models
from apps.clients.models import Client
from apps.comptes.models import Compte
from apps.accounts.models import Utilisateur
from decimal import Decimal

class Carte31(models.Model):
    """
    Carte spéciale à 31 cases.
    Le client remplit 30 cases (montants libres).
    La case 31 appartient à la microfinance (retenue à la clôture).
    """
    STATUT = [('active','Active'),('complete','Complète — En attente clôture'),('cloturee','Clôturée'),('annulee','Annulée')]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='cartes_31')
    compte = models.ForeignKey(Compte, on_delete=models.PROTECT, related_name='cartes_31')
    numero = models.CharField(max_length=20, unique=True)
    statut = models.CharField(max_length=15, choices=STATUT, default='active')
    montant_case_31 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Montant retenu par la microfinance (dernière case à la clôture)")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_cloture = models.DateTimeField(null=True, blank=True)
    agent_creation = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='cartes_creees')
    agent_cloture = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='cartes_cloturees')
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            import random
            self.numero = f"C31-{random.randint(100000,999999)}"
        super().save(*args, **kwargs)

    @property
    def cases_remplies(self):
        return self.cases.filter(remplie=True).count()

    @property
    def total_depose(self):
        return sum(c.montant for c in self.cases.filter(remplie=True))

    @property
    def montant_client(self):
        """Montant que reçoit le client (30 cases, la 31e est pour la MF)"""
        cases = sorted(self.cases.filter(remplie=True), key=lambda c: c.montant)
        # On enlève la case de plus grande valeur (ou dernière déposée selon règle)
        if len(cases) >= 1:
            return sum(c.montant for c in cases[:-1])
        return Decimal('0')

    @property
    def est_complete(self):
        return self.cases_remplies >= 31

    @property
    def progression_pct(self):
        return round(self.cases_remplies / 31 * 100)

    def __str__(self):
        return f"{self.numero} — {self.client} ({self.cases_remplies}/31)"

    class Meta:
        ordering = ['-date_creation']


class CaseDepot(models.Model):
    """Une case individuelle de la carte 31"""
    carte = models.ForeignKey(Carte31, on_delete=models.CASCADE, related_name='cases')
    numero_case = models.IntegerField()  # 1 à 31
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    remplie = models.BooleanField(default=True)
    date_depot = models.DateTimeField(auto_now_add=True)
    caissier = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Case {self.numero_case} — {self.carte.numero} — {self.montant} FCFA"

    class Meta:
        ordering = ['numero_case']
        unique_together = ['carte', 'numero_case']
