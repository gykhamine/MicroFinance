from django.db import models
from apps.accounts.models import Utilisateur
import qrcode, io
from django.core.files.base import ContentFile

class Client(models.Model):
    STATUT = [('actif','Actif'),('suspendu','Suspendu'),('cloture','Clôturé')]
    TYPE_PIECE = [('cni','CNI'),('passeport','Passeport'),('permis','Permis de conduire'),('autre','Autre')]

    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='profil_client')
    numero_client = models.CharField(max_length=20, unique=True)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=100, blank=True)
    type_piece = models.CharField(max_length=20, choices=TYPE_PIECE, blank=True)
    numero_piece = models.CharField(max_length=50, blank=True)
    profession = models.CharField(max_length=100, blank=True)
    employeur = models.CharField(max_length=100, blank=True)
    revenu_mensuel = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=STATUT, default='actif')
    agent_ouverture = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='clients_ouverts')
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    date_adhesion = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.numero_client:
            import random
            self.numero_client = f"CLI{random.randint(100000,999999)}"
        if not self.qr_code:
            self._gen_qr()
        super().save(*args, **kwargs)

    def _gen_qr(self):
        qr = qrcode.QRCode(version=1, box_size=8, border=3)
        qr.add_data(f"MF:{self.numero_client}|{self.utilisateur.get_full_name()}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        self.qr_code.save(f'qr_{self.numero_client}.png', ContentFile(buf.getvalue()), save=False)

    def solde_total(self):
        return sum(c.solde for c in self.comptes.filter(actif=True))

    def __str__(self):
        return f"{self.utilisateur.get_full_name()} [{self.numero_client}]"

    class Meta:
        ordering = ['-date_adhesion']
