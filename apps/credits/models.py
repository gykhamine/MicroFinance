from django.db import models
from apps.clients.models import Client
from apps.comptes.models import Compte
from apps.accounts.models import Utilisateur
from decimal import Decimal
from datetime import date

class TypeCredit(models.Model):
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    taux_interet_mensuel = models.DecimalField(max_digits=5, decimal_places=3)
    duree_max_mois = models.IntegerField(default=24)
    montant_min = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_max = models.DecimalField(max_digits=12, decimal_places=2, default=5000000)
    garantie_requise = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    def __str__(self): return f"{self.code} — {self.nom}"

class DemandeCredit(models.Model):
    STATUT = [('soumise','Soumise'),('en_etude','En étude'),('approuvee','Approuvée'),('rejetee','Rejetée'),('decaissee','Décaissée'),('cloturee','Clôturée')]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='demandes_credit')
    type_credit = models.ForeignKey(TypeCredit, on_delete=models.PROTECT)
    compte_decaissement = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, blank=True)
    montant_demande = models.DecimalField(max_digits=12, decimal_places=2)
    montant_accorde = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    duree_mois = models.IntegerField()
    taux_interet_mensuel = models.DecimalField(max_digits=5, decimal_places=3)
    objet_credit = models.TextField()
    garantie = models.TextField(blank=True)
    statut = models.CharField(max_length=12, choices=STATUT, default='soumise')
    agent_instruction = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='credits_instruits')
    agent_decision = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='credits_decides')
    date_demande = models.DateTimeField(auto_now_add=True)
    date_decision = models.DateTimeField(null=True, blank=True)
    date_decaissement = models.DateTimeField(null=True, blank=True)
    motif_rejet = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def mensualite(self):
        if not self.montant_accorde: return Decimal('0')
        M = Decimal(str(self.montant_accorde))
        r = Decimal(str(self.taux_interet_mensuel)) / 100
        n = self.duree_mois
        if r == 0: return M / n
        return M * r * (1 + r)**n / ((1 + r)**n - 1)

    def total_remboursement(self):
        return self.mensualite() * self.duree_mois

    def total_interets(self):
        if not self.montant_accorde: return Decimal('0')
        return self.total_remboursement() - (self.montant_accorde or 0)

    def __str__(self):
        return f"Crédit {self.pk} — {self.client} — {self.montant_demande} FCFA"

    class Meta:
        ordering = ['-date_demande']

class Echeance(models.Model):
    STATUT = [('a_venir','À venir'),('en_retard','En retard'),('payee','Payée'),('partiel','Partiel')]
    demande = models.ForeignKey(DemandeCredit, on_delete=models.CASCADE, related_name='echeances')
    numero = models.IntegerField()
    date_echeance = models.DateField()
    montant_principal = models.DecimalField(max_digits=12, decimal_places=2)
    montant_interet = models.DecimalField(max_digits=12, decimal_places=2)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    montant_paye = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_paiement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT, default='a_venir')
    penalite = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def reste_a_payer(self):
        return self.montant_total + self.penalite - self.montant_paye

    @property
    def est_en_retard(self):
        return self.statut != 'payee' and self.date_echeance < date.today()

    def __str__(self):
        return f"Échéance {self.numero} — {self.demande.client} — {self.montant_total} FCFA"

    class Meta:
        ordering = ['numero']
