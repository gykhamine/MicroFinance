from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Carte31, CaseDepot
from apps.clients.models import Client
from apps.comptes.models import Compte
from apps.accounts.decorators import staff_only, caissier_only
from apps.transactions.services import depot as service_depot, cloture_carte_31

@login_required
@staff_only
def liste_cartes(request):
    statut = request.GET.get('statut','active')
    cartes = Carte31.objects.select_related('client__utilisateur').all()
    if statut: cartes = cartes.filter(statut=statut)
    return render(request, 'cartes_31/liste.html', {'cartes': cartes, 'statut_filtre': statut})

@login_required
def detail_carte(request, pk):
    carte = get_object_or_404(Carte31, pk=pk)
    if request.user.role == 'client':
        if carte.client.utilisateur != request.user:
            return redirect('dashboard')
    cases_list = list(carte.cases.filter(remplie=True))
    cases_remplies = {c.numero_case: c for c in cases_list}
    import json
    cases_remplies_json = json.dumps({c.numero_case: float(c.montant) for c in cases_list})
    return render(request, 'cartes_31/detail.html', {
        'carte': carte,
        'cases_remplies': cases_remplies,
        'cases_range': range(1, 32),
        'cases_remplies_json': cases_remplies_json,
    })

@login_required
@caissier_only
def creer_carte(request):
    if request.method == 'POST':
        client = get_object_or_404(Client, pk=request.POST['client'])
        compte = get_object_or_404(Compte, pk=request.POST['compte'])
        carte = Carte31.objects.create(client=client, compte=compte, agent_creation=request.user, notes=request.POST.get('notes',''))
        messages.success(request, f"Carte {carte.numero} créée pour {client}.")
        return redirect('detail_carte', pk=carte.pk)
    clients = Client.objects.filter(statut='actif').select_related('utilisateur').prefetch_related('comptes')
    return render(request, 'cartes_31/form_creation.html', {'clients': clients})

@login_required
@caissier_only
def deposer_case(request, pk):
    carte = get_object_or_404(Carte31, pk=pk, statut='active')
    if request.method == 'POST':
        try:
            num_case = int(request.POST['numero_case'])
            montant = request.POST['montant']
            if carte.cases.filter(numero_case=num_case).exists():
                raise ValueError(f"La case {num_case} est déjà remplie.")
            if num_case < 1 or num_case > 31:
                raise ValueError("Numéro de case invalide (1-31).")
            # Créer la case
            CaseDepot.objects.create(carte=carte, numero_case=num_case, montant=montant, caissier=request.user)
            # Transaction dépôt sur le compte
            service_depot(carte.compte, montant, request.user, f"Carte {carte.numero} — Case {num_case}", carte_31=carte)
            # Mettre à jour statut si complète
            if carte.cases_remplies >= 31:
                carte.statut = 'complete'
                carte.save()
                messages.success(request, f"✅ Case {num_case} remplie. Carte COMPLÈTE ! Procéder à la clôture.")
            else:
                messages.success(request, f"✅ Case {num_case} — {float(montant):,.0f} FCFA. {carte.cases_remplies}/31 cases remplies.")
            return redirect('detail_carte', pk=pk)
        except Exception as e:
            messages.error(request, str(e))
    cases_libres = [i for i in range(1, 32) if not carte.cases.filter(numero_case=i).exists()]
    return render(request, 'cartes_31/deposer_case.html', {'carte': carte, 'cases_libres': cases_libres, 'cases_range': range(1,32)})

@login_required
@caissier_only
def cloturer_carte(request, pk):
    carte = get_object_or_404(Carte31, pk=pk, statut='complete')
    if request.method == 'POST':
        try:
            montant_client, montant_mf = cloture_carte_31(carte, request.user)
            messages.success(request, f"✅ Carte clôturée ! Client reçoit : {montant_client:,.0f} FCFA | Microfinance retient : {montant_mf:,.0f} FCFA (case 31)")
            return redirect('detail_client', pk=carte.client.pk)
        except Exception as e:
            messages.error(request, str(e))
    # Preview clôture
    cases = sorted(carte.cases.filter(remplie=True), key=lambda c: c.montant)
    case_mf = cases[-1] if cases else None
    montant_client_preview = sum(c.montant for c in cases[:-1]) if len(cases) > 1 else 0
    return render(request, 'cartes_31/cloture.html', {
        'carte': carte, 'cases': cases, 'case_mf': case_mf,
        'montant_client_preview': montant_client_preview,
    })
