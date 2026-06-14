"""Service layer pour toutes les opérations bancaires — source unique de vérité"""
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from .models import Transaction, ParametresTaxe
from apps.comptes.models import Compte

def _get_frais(type_op, montant):
    taxe = ParametresTaxe.objects.filter(type_operation=type_op, actif=True).first()
    if taxe:
        return taxe.calculer(montant)
    return Decimal('0')

@db_transaction.atomic
def depot(compte, montant, caissier, description='', carte_31=None):
    montant = Decimal(str(montant))
    frais = _get_frais('depot', montant)
    solde_avant = compte.solde
    compte.solde += montant - frais
    compte.save()
    type_t = 'carte_depot' if carte_31 else 'depot'
    t = Transaction.objects.create(
        compte=compte, type_transaction=type_t,
        montant=montant, frais=frais,
        solde_avant=solde_avant, solde_apres=compte.solde,
        description=description, caissier=caissier,
        carte_31=carte_31,
    )
    return t

@db_transaction.atomic
def retrait(compte, montant, caissier, description=''):
    montant = Decimal(str(montant))
    frais = _get_frais('retrait', montant)
    total_debite = montant + frais
    if compte.solde < total_debite:
        raise ValueError(f"Solde insuffisant. Disponible: {compte.solde} FCFA, Requis: {total_debite} FCFA")
    solde_avant = compte.solde
    compte.solde -= total_debite
    compte.save()
    t = Transaction.objects.create(
        compte=compte, type_transaction='retrait',
        montant=montant, frais=frais,
        solde_avant=solde_avant, solde_apres=compte.solde,
        description=description, caissier=caissier,
    )
    return t

@db_transaction.atomic
def transfert(compte_source, compte_dest, montant, caissier, description=''):
    montant = Decimal(str(montant))
    frais = _get_frais('transfert', montant)
    total_debite = montant + frais
    if compte_source.solde < total_debite:
        raise ValueError(f"Solde insuffisant. Disponible: {compte_source.solde} FCFA")
    if compte_source.client == compte_dest.client:
        raise ValueError("Impossible de transférer vers le même client.")
    # Débit source
    s_avant = compte_source.solde
    compte_source.solde -= total_debite
    compte_source.save()
    t_debit = Transaction.objects.create(
        compte=compte_source, type_transaction='transfert_debit',
        montant=montant, frais=frais,
        solde_avant=s_avant, solde_apres=compte_source.solde,
        description=f"Transfert vers {compte_dest.numero} — {description}",
        caissier=caissier, compte_lie=compte_dest,
    )
    # Crédit destination
    d_avant = compte_dest.solde
    compte_dest.solde += montant
    compte_dest.save()
    Transaction.objects.create(
        compte=compte_dest, type_transaction='transfert_credit',
        montant=montant, frais=Decimal('0'),
        solde_avant=d_avant, solde_apres=compte_dest.solde,
        description=f"Transfert reçu de {compte_source.numero} — {description}",
        caissier=caissier, compte_lie=compte_source,
    )
    return t_debit

@db_transaction.atomic
def cloture_carte_31(carte, caissier):
    """
    Clôture une carte 31 :
    - Trie les cases par montant croissant
    - La case au montant le plus élevé va à la microfinance (case 31)
    - Les 30 autres sont versées au client
    """
    from apps.cartes_31.models import CaseDepot
    cases = list(carte.cases.filter(remplie=True).order_by('montant'))
    if len(cases) < 31:
        raise ValueError(f"La carte n'est pas complète ({len(cases)}/31 cases).")
    # La case 31 (plus grande valeur) revient à la MF
    case_mf = cases[-1]
    montant_client = sum(c.montant for c in cases[:-1])
    montant_mf = case_mf.montant
    # Créditer le compte client
    frais = _get_frais('carte_31', carte.total_depose)
    compte = carte.compte
    s_avant = compte.solde
    compte.solde += montant_client
    compte.save()
    Transaction.objects.create(
        compte=compte, type_transaction='carte_cloture',
        montant=montant_client, frais=montant_mf,
        solde_avant=s_avant, solde_apres=compte.solde,
        description=f"Clôture carte {carte.numero} — Case 31 retenue: {montant_mf} FCFA",
        caissier=caissier, carte_31=carte,
    )
    carte.montant_case_31 = montant_mf
    carte.statut = 'cloturee'
    carte.date_cloture = timezone.now()
    carte.agent_cloture = caissier
    carte.save()
    return montant_client, montant_mf

@db_transaction.atomic
def rembourser_echeance(echeance, montant_paye, caissier):
    from apps.credits.models import Echeance
    from decimal import Decimal
    montant_paye = Decimal(str(montant_paye))
    compte = echeance.demande.compte_decaissement
    if compte.solde < montant_paye:
        raise ValueError("Solde insuffisant pour ce remboursement.")
    s_avant = compte.solde
    compte.solde -= montant_paye
    compte.save()
    Transaction.objects.create(
        compte=compte, type_transaction='remboursement',
        montant=montant_paye, frais=Decimal('0'),
        solde_avant=s_avant, solde_apres=compte.solde,
        description=f"Remboursement échéance {echeance.numero} — Crédit #{echeance.demande.pk}",
        caissier=caissier,
    )
    echeance.montant_paye += montant_paye
    if echeance.montant_paye >= echeance.reste_a_payer() + montant_paye:
        echeance.statut = 'payee'
        from datetime import date
        echeance.date_paiement = date.today()
    else:
        echeance.statut = 'partiel'
    echeance.save()
    # Vérifier si toutes les échéances sont payées
    demande = echeance.demande
    if not demande.echeances.exclude(statut='payee').exists():
        demande.statut = 'cloturee'
        demande.save()
    return echeance
