from django.db import models
from apps.comptes.models import Compte
from apps.accounts.models import Utilisateur
from decimal import Decimal

class ParametresTaxe(models.Model):
    """Paramètres configurables des taxes et frais"""
    nom = models.CharField(max_length=100)
    type_operation = models.CharField(max_length=30, choices=[
        ('depot','Dépôt'),('retrait','Retrait'),('transfert','Transfert'),
        ('credit','Remboursement crédit'),('carte_31','Carte 31'),
    ])
    taux_pourcent = models.DecimalField(max_digits=5, decimal_places=3, default=0,
        help_text="Taux en % (ex: 1.5 pour 1.5%)")
    montant_fixe = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text="Frais fixe en FCFA")
    montant_minimum = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text="Frais minimum")
    actif = models.BooleanField(default=True)

    def calculer(self, montant):
        frais = Decimal(str(montant)) * (self.taux_pourcent / 100) + self.montant_fixe
        return max(frais, self.montant_minimum)

    def __str__(self):
        return f"{self.nom} ({self.get_type_operation_display()})"


class Transaction(models.Model):
    TYPE = [
        ('depot','Dépôt'),('retrait','Retrait'),
        ('transfert_debit','Transfert (débit)'),('transfert_credit','Transfert (crédit)'),
        ('frais','Frais / Taxe'),('interet','Intérêt'),
        ('remboursement','Remboursement crédit'),
        ('decaissement','Décaissement crédit'),
        ('carte_depot','Dépôt Carte 31'),('carte_cloture','Clôture Carte 31'),
    ]
    STATUT = [('en_attente','En attente'),('validee','Validée'),('rejetee','Rejetée'),('annulee','Annulée')]

    compte = models.ForeignKey(Compte, on_delete=models.PROTECT, related_name='transactions')
    type_transaction = models.CharField(max_length=25, choices=TYPE)
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    frais = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    solde_avant = models.DecimalField(max_digits=14, decimal_places=2)
    solde_apres = models.DecimalField(max_digits=14, decimal_places=2)
    statut = models.CharField(max_length=12, choices=STATUT, default='validee')
    reference = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    compte_lie = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transactions_liees', help_text="Compte destination pour transferts")
    caissier = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='transactions_effectuees')
    date = models.DateTimeField(auto_now_add=True)
    carte_31 = models.ForeignKey('cartes_31.Carte31', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')

    def save(self, *args, **kwargs):
        if not self.reference:
            import random, datetime
            self.reference = f"TXN{datetime.datetime.now().strftime('%Y%m%d')}{random.randint(10000,99999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.get_type_transaction_display()} {self.montant} FCFA"

    class Meta:
        ordering = ['-date']
