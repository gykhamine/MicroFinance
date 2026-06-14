from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PlanEpargne, VersementEpargne
from apps.clients.models import Client
from apps.comptes.models import Compte
from apps.accounts.decorators import staff_only, caissier_only

@login_required
@staff_only
def liste_plans(request):
    plans = PlanEpargne.objects.select_related('client__utilisateur').filter(actif=True)
    return render(request, 'epargne/liste.html', {'plans': plans})

@login_required
def detail_plan(request, pk):
    plan = get_object_or_404(PlanEpargne, pk=pk)
    if request.user.role == 'client':
        if plan.client.utilisateur != request.user:
            return redirect('dashboard')
    return render(request, 'epargne/detail.html', {'plan': plan})

@login_required
@caissier_only
def creer_plan(request):
    if request.method == 'POST':
        client = get_object_or_404(Client, pk=request.POST['client'])
        compte = get_object_or_404(Compte, pk=request.POST['compte'])
        PlanEpargne.objects.create(
            client=client, compte=compte,
            nom=request.POST['nom'],
            objectif=request.POST['objectif'],
            montant_verse=request.POST['montant_verse'],
            frequence=request.POST['frequence'],
            date_debut=request.POST['date_debut'],
            date_fin_prevue=request.POST.get('date_fin_prevue') or None,
            agent=request.user,
        )
        messages.success(request, "Plan d'épargne créé.")
        return redirect('liste_plans')
    clients = Client.objects.filter(statut='actif').select_related('utilisateur').prefetch_related('comptes')
    return render(request, 'epargne/form.html', {'clients': clients})

@login_required
@caissier_only
def ajouter_versement(request, pk):
    plan = get_object_or_404(PlanEpargne, pk=pk, actif=True)
    if request.method == 'POST':
        montant = request.POST['montant']
        from apps.transactions.services import depot
        depot(plan.compte, montant, request.user, f"Versement épargne — {plan.nom}")
        VersementEpargne.objects.create(plan=plan, montant=montant, caissier=request.user)
        messages.success(request, f"✅ Versement de {float(montant):,.0f} FCFA enregistré.")
        return redirect('detail_plan', pk=pk)
    return render(request, 'epargne/versement.html', {'plan': plan})
