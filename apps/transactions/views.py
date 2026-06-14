from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Transaction, ParametresTaxe
from .services import depot, retrait, transfert
from apps.comptes.models import Compte
from apps.clients.models import Client
from apps.accounts.decorators import staff_only, caissier_only, directeur_only

@login_required
@caissier_only
def faire_depot(request):
    if request.method == 'POST':
        compte = get_object_or_404(Compte, pk=request.POST['compte'], statut='actif')
        try:
            t = depot(compte, request.POST['montant'], request.user, request.POST.get('description','Dépôt espèces'))
            messages.success(request, f"✅ Dépôt de {t.montant:,.0f} FCFA effectué. Nouveau solde : {t.solde_apres:,.0f} FCFA")
            return redirect('detail_client', pk=compte.client.pk)
        except Exception as e:
            messages.error(request, str(e))
    clients = Client.objects.filter(statut='actif').select_related('utilisateur').prefetch_related('comptes')
    return render(request, 'transactions/depot.html', {'clients': clients})

@login_required
@caissier_only
def faire_retrait(request):
    if request.method == 'POST':
        compte = get_object_or_404(Compte, pk=request.POST['compte'], statut='actif')
        try:
            t = retrait(compte, request.POST['montant'], request.user, request.POST.get('description','Retrait espèces'))
            messages.success(request, f"✅ Retrait de {t.montant:,.0f} FCFA effectué. Nouveau solde : {t.solde_apres:,.0f} FCFA")
            return redirect('detail_client', pk=compte.client.pk)
        except Exception as e:
            messages.error(request, str(e))
    clients = Client.objects.filter(statut='actif').select_related('utilisateur').prefetch_related('comptes')
    return render(request, 'transactions/retrait.html', {'clients': clients})

@login_required
@caissier_only
def faire_transfert(request):
    if request.method == 'POST':
        source = get_object_or_404(Compte, pk=request.POST['compte_source'], statut='actif')
        dest = get_object_or_404(Compte, numero=request.POST['compte_dest_numero'], statut='actif')
        try:
            t = transfert(source, dest, request.POST['montant'], request.user, request.POST.get('description','Transfert interne'))
            messages.success(request, f"✅ Transfert de {t.montant:,.0f} FCFA vers {dest.numero}. Frais : {t.frais:,.0f} FCFA")
            return redirect('detail_client', pk=source.client.pk)
        except Exception as e:
            messages.error(request, str(e))
    clients = Client.objects.filter(statut='actif').select_related('utilisateur').prefetch_related('comptes')
    return render(request, 'transactions/transfert.html', {'clients': clients})

@login_required
@staff_only
def journal_transactions(request):
    from django.db.models import Sum
    txns = Transaction.objects.select_related('compte__client__utilisateur','caissier').all()
    type_f = request.GET.get('type','')
    date_f = request.GET.get('date','')
    if type_f: txns = txns.filter(type_transaction=type_f)
    if date_f: txns = txns.filter(date__date=date_f)
    total_depots = txns.filter(type_transaction='depot').aggregate(s=Sum('montant'))['s'] or 0
    total_retraits = txns.filter(type_transaction='retrait').aggregate(s=Sum('montant'))['s'] or 0
    total_frais = txns.aggregate(s=Sum('frais'))['s'] or 0
    return render(request, 'transactions/journal.html', {
        'transactions': txns[:100],
        'total_depots': total_depots, 'total_retraits': total_retraits, 'total_frais': total_frais,
        'type_filtre': type_f, 'date_filtre': date_f,
    })

@login_required
@directeur_only
def gestion_taxes(request):
    taxes = ParametresTaxe.objects.all()
    if request.method == 'POST':
        if request.POST.get('action') == 'toggle':
            t = get_object_or_404(ParametresTaxe, pk=request.POST['pk'])
            t.actif = not t.actif
            t.save()
            messages.success(request, f"Taxe {'activée' if t.actif else 'désactivée'}.")
        elif request.POST.get('action') == 'update':
            t = get_object_or_404(ParametresTaxe, pk=request.POST['pk'])
            t.taux_pourcent = request.POST.get('taux_pourcent', t.taux_pourcent)
            t.montant_fixe = request.POST.get('montant_fixe', t.montant_fixe)
            t.montant_minimum = request.POST.get('montant_minimum', t.montant_minimum)
            t.save()
            messages.success(request, "Taxe mise à jour.")
        elif request.POST.get('action') == 'creer':
            ParametresTaxe.objects.create(
                nom=request.POST['nom'],
                type_operation=request.POST['type_operation'],
                taux_pourcent=request.POST.get('taux_pourcent',0),
                montant_fixe=request.POST.get('montant_fixe',0),
                montant_minimum=request.POST.get('montant_minimum',0),
            )
            messages.success(request, "Taxe créée.")
    return render(request, 'transactions/taxes.html', {'taxes': taxes})

def get_comptes_client(request):
    """AJAX — retourne les comptes actifs d'un client"""
    client_id = request.GET.get('client_id')
    comptes = Compte.objects.filter(client_id=client_id, statut='actif').values('pk','numero','solde','type_compte__nom')
    return JsonResponse({'comptes': list(comptes)})
