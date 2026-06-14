from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .models import DemandeCredit, TypeCredit, Echeance
from apps.clients.models import Client
from apps.comptes.models import Compte
from apps.accounts.decorators import staff_only, preteur_only, directeur_only, caissier_only

@login_required
@staff_only
def liste_credits(request):
    statut = request.GET.get('statut', '')
    credits = DemandeCredit.objects.select_related('client__utilisateur','type_credit').all()
    if statut: credits = credits.filter(statut=statut)
    return render(request, 'credits/liste.html', {'credits': credits, 'statut_filtre': statut})

@login_required
def detail_credit(request, pk):
    credit = get_object_or_404(DemandeCredit, pk=pk)
    if request.user.role == 'client':
        if credit.client.utilisateur != request.user:
            return redirect('dashboard')
    echeances = credit.echeances.all()
    steps = [
        ('1', 'Demande soumise', credit.date_demande.strftime('%d/%m/%Y') if credit.date_demande else None, None),
        ('2', 'Décision prise', credit.date_decision.strftime('%d/%m/%Y') if credit.date_decision else None, str(credit.agent_decision) if credit.agent_decision else None),
        ('3', 'Décaissé', credit.date_decaissement.strftime('%d/%m/%Y') if credit.date_decaissement else None, None),
    ]
    return render(request, 'credits/detail.html', {'credit': credit, 'echeances': echeances, 'steps': steps})

@login_required
@caissier_only
def soumettre_demande(request):
    if request.method == 'POST':
        client = get_object_or_404(Client, pk=request.POST['client'])
        type_c = get_object_or_404(TypeCredit, pk=request.POST['type_credit'])
        compte = get_object_or_404(Compte, pk=request.POST['compte'])
        DemandeCredit.objects.create(
            client=client, type_credit=type_c,
            compte_decaissement=compte,
            montant_demande=request.POST['montant_demande'],
            duree_mois=request.POST['duree_mois'],
            taux_interet_mensuel=type_c.taux_interet_mensuel,
            objet_credit=request.POST['objet_credit'],
            garantie=request.POST.get('garantie',''),
            agent_instruction=request.user,
            notes=request.POST.get('notes',''),
        )
        messages.success(request, "Demande de crédit soumise.")
        return redirect('liste_credits')
    clients = Client.objects.filter(statut='actif').select_related('utilisateur').prefetch_related('comptes')
    types = TypeCredit.objects.filter(actif=True)
    return render(request, 'credits/form_demande.html', {'clients': clients, 'types': types})

@login_required
@preteur_only
def instruire_credit(request, pk):
    credit = get_object_or_404(DemandeCredit, pk=pk, statut__in=['soumise','en_etude'])
    if request.method == 'POST':
        decision = request.POST['decision']
        if decision == 'approuver':
            credit.montant_accorde = request.POST.get('montant_accorde', credit.montant_demande)
            credit.statut = 'approuvee'
        else:
            credit.statut = 'rejetee'
            credit.motif_rejet = request.POST.get('motif_rejet','')
        credit.agent_decision = request.user
        credit.date_decision = timezone.now()
        credit.notes = request.POST.get('notes', credit.notes)
        credit.save()
        # Notif client
        from apps.notifications.models import Notification
        Notification.objects.create(
            destinataire=credit.client.utilisateur,
            titre=f"Crédit {'approuvé' if decision=='approuver' else 'rejeté'}",
            message=f"Votre demande de {credit.montant_demande:,.0f} FCFA a été {'approuvée' if decision=='approuver' else 'rejetée'}.",
            type_notif='info',
        )
        messages.success(request, f"Crédit {credit.get_statut_display()}.")
        return redirect('detail_credit', pk=pk)
    return render(request, 'credits/instruire.html', {'credit': credit})

@login_required
@preteur_only
def decaisser_credit(request, pk):
    credit = get_object_or_404(DemandeCredit, pk=pk, statut='approuvee')
    if request.method == 'POST':
        from apps.transactions.services import depot
        compte = credit.compte_decaissement
        montant = credit.montant_accorde
        depot(compte, montant, request.user, f"Décaissement crédit #{credit.pk}")
        credit.statut = 'decaissee'
        credit.date_decaissement = timezone.now()
        credit.save()
        # Générer le tableau d'amortissement
        _generer_echeances(credit)
        messages.success(request, f"✅ Crédit décaissé — {montant:,.0f} FCFA versés.")
        return redirect('detail_credit', pk=pk)
    return render(request, 'credits/decaisser.html', {'credit': credit})

def _generer_echeances(credit):
    from decimal import Decimal
    M = credit.montant_accorde
    r = Decimal(str(credit.taux_interet_mensuel)) / 100
    n = credit.duree_mois
    mensualite = credit.mensualite()
    solde_restant = M
    date_debut = credit.date_decaissement.date()
    for i in range(1, n + 1):
        interet = solde_restant * r
        principal = mensualite - interet
        if i == n:
            principal = solde_restant
            total = principal + interet
        else:
            total = mensualite
        Echeance.objects.create(
            demande=credit, numero=i,
            date_echeance=date_debut + timedelta(days=30*i),
            montant_principal=round(principal, 2),
            montant_interet=round(interet, 2),
            montant_total=round(total, 2),
        )
        solde_restant -= principal

@login_required
@caissier_only
def rembourser_echeance_view(request, pk):
    echeance = get_object_or_404(Echeance, pk=pk)
    if request.user.role == 'client':
        if echeance.demande.client.utilisateur != request.user:
            return redirect('dashboard')
    if request.method == 'POST':
        try:
            from apps.transactions.services import rembourser_echeance
            montant = request.POST.get('montant', echeance.reste_a_payer())
            rembourser_echeance(echeance, montant, request.user)
            messages.success(request, f"✅ Remboursement de {float(montant):,.0f} FCFA enregistré.")
            return redirect('detail_credit', pk=echeance.demande.pk)
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'credits/remboursement.html', {'echeance': echeance})

@login_required
@directeur_only
def gestion_types_credit(request):
    types = TypeCredit.objects.all()
    if request.method == 'POST':
        TypeCredit.objects.create(
            nom=request.POST['nom'], code=request.POST['code'].upper(),
            taux_interet_mensuel=request.POST['taux_interet_mensuel'],
            duree_max_mois=request.POST.get('duree_max_mois',24),
            montant_min=request.POST.get('montant_min',0),
            montant_max=request.POST.get('montant_max',5000000),
            garantie_requise=request.POST.get('garantie_requise')=='on',
            description=request.POST.get('description',''),
        )
        messages.success(request, "Type de crédit créé.")
    return render(request, 'credits/types.html', {'types': types})

@login_required
@staff_only
def tableau_amortissement(request, pk):
    credit = get_object_or_404(DemandeCredit, pk=pk)
    echeances = credit.echeances.all()
    total_paye = sum(e.montant_paye for e in echeances)
    total_restant = sum(e.reste_a_payer() for e in echeances if e.statut != 'payee')
    return render(request, 'credits/amortissement.html', {
        'credit': credit, 'echeances': echeances,
        'total_paye': total_paye, 'total_restant': total_restant,
    })
