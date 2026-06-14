from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Compte, TypeCompte
from apps.clients.models import Client
from apps.accounts.decorators import staff_only, caissier_only, directeur_only

@login_required
@caissier_only
def ouvrir_compte(request):
    if request.method == 'POST':
        client = get_object_or_404(Client, pk=request.POST['client'])
        type_c = get_object_or_404(TypeCompte, pk=request.POST['type_compte'])
        c = Compte.objects.create(client=client, type_compte=type_c, agent_ouverture=request.user, notes=request.POST.get('notes',''))
        # Frais d'ouverture
        if type_c.frais_ouverture > 0:
            from apps.transactions.services import depot
            depot(c, type_c.frais_ouverture, request.user, "Frais d'ouverture de compte")
        messages.success(request, f"Compte {c.numero} ouvert.")
        return redirect('detail_client', pk=client.pk)
    clients = Client.objects.filter(statut='actif').select_related('utilisateur')
    types = TypeCompte.objects.filter(actif=True)
    return render(request, 'comptes/form_ouverture.html', {'clients': clients, 'types': types})

@login_required
@staff_only
def detail_compte(request, pk):
    compte = get_object_or_404(Compte, pk=pk)
    if request.user.role == 'client':
        if compte.client.utilisateur != request.user:
            return redirect('dashboard')
    transactions = compte.transactions.all()[:30]
    return render(request, 'comptes/detail.html', {'compte': compte, 'transactions': transactions})

@login_required
@directeur_only
def gestion_types_comptes(request):
    types = TypeCompte.objects.all()
    if request.method == 'POST':
        TypeCompte.objects.create(
            nom=request.POST['nom'], code=request.POST['code'].upper(),
            solde_minimum=request.POST.get('solde_minimum',0),
            frais_ouverture=request.POST.get('frais_ouverture',0),
            taux_interet_annuel=request.POST.get('taux_interet_annuel',0),
            description=request.POST.get('description',''),
        )
        messages.success(request, "Type de compte créé.")
    return render(request, 'comptes/types.html', {'types': types})
