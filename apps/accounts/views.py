from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Utilisateur
from .decorators import directeur_only, staff_only

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user and user.actif:
            login(request, user)
            return redirect('dashboard')
        error = "Identifiants invalides ou compte désactivé."
    return render(request, 'accounts/login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    from apps.clients.models import Client
    from apps.comptes.models import Compte
    from apps.transactions.models import Transaction
    from apps.credits.models import DemandeCredit, Echeance
    from apps.cartes_31.models import Carte31
    from apps.notifications.models import Notification
    from django.utils import timezone
    from datetime import date, timedelta
    ctx = {'user': request.user}

    if request.user.role == 'client':
        try:
            client = request.user.profil_client
            ctx['comptes'] = client.comptes.filter(actif=True)
            ctx['solde_total'] = client.solde_total()
            ctx['transactions_recentes'] = Transaction.objects.filter(compte__client=client)[:8]
            ctx['cartes_actives'] = client.cartes_31.filter(statut__in=['active','complete'])
            ctx['credits_actifs'] = client.demandes_credit.filter(statut__in=['decaissee'])
            ctx['echeances_proches'] = Echeance.objects.filter(
                demande__client=client, statut__in=['a_venir','en_retard'],
                date_echeance__lte=date.today()+timedelta(days=15)
            ).order_by('date_echeance')[:5]
        except: pass
    else:
        ctx['nb_clients'] = Client.objects.filter(statut='actif').count()
        ctx['nb_comptes'] = Compte.objects.filter(actif=True).count()
        ctx['total_depots'] = sum(c.solde for c in Compte.objects.filter(actif=True))
        ctx['credits_en_cours'] = DemandeCredit.objects.filter(statut='decaissee').count()
        ctx['echeances_retard'] = Echeance.objects.filter(statut='en_retard').count()
        ctx['cartes_actives'] = Carte31.objects.filter(statut__in=['active','complete']).count()
        ctx['transactions_aujourd_hui'] = Transaction.objects.filter(date__date=date.today()).count()
        ctx['transactions_recentes'] = Transaction.objects.select_related('compte__client__utilisateur','caissier')[:10]
        if request.user.role in ['preteur','directeur']:
            ctx['demandes_en_attente'] = DemandeCredit.objects.filter(statut__in=['soumise','en_etude'])[:5]
        if request.user.role in ['caissier','banque','directeur']:
            ctx['echeances_aujourd_hui'] = Echeance.objects.filter(date_echeance=date.today(), statut__in=['a_venir','en_retard'])[:5]

    ctx['notifications'] = Notification.objects.filter(destinataire=request.user, lue=False)[:5]
    return render(request, 'accounts/dashboard.html', ctx)

@login_required
@directeur_only
def liste_utilisateurs(request):
    users = Utilisateur.objects.all()
    return render(request, 'accounts/utilisateurs.html', {'utilisateurs': users})

@login_required
@directeur_only
def creer_utilisateur(request):
    if request.method == 'POST':
        u = Utilisateur.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password'],
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=request.POST.get('email',''),
            telephone=request.POST.get('telephone',''),
            role=request.POST['role'],
        )
        messages.success(request, f"Compte {u.get_full_name()} créé.")
        return redirect('liste_utilisateurs')
    return render(request, 'accounts/form_utilisateur.html')

@login_required
def mon_profil(request):
    droits_par_role = {
        'directeur': ['Accès total', 'Gestion des utilisateurs', 'Configuration taxes et frais', 'Rapports complets', 'Approbation et rejet crédits', 'Décaissements'],
        'banque': ['Toutes les opérations de caisse', 'Instruction et décaissement crédits', 'Journal des transactions', 'Gestion cartes 31'],
        'caissier': ['Dépôts espèces', 'Retraits espèces', 'Transferts internes', 'Nouveaux clients', 'Cartes 31 (créer, déposer, clôturer)', 'Encaissement échéances'],
        'preteur': ['Instruction des demandes de crédit', 'Décaissements', 'Suivi des remboursements', 'Tableau d\'amortissement'],
        'client': ['Consultation solde et transactions', 'Suivi cartes 31', 'Suivi crédits', 'Suivi épargne'],
    }
    droits = droits_par_role.get(request.user.role, [])
    return render(request, 'accounts/profil.html', {'u': request.user, 'droits': droits})

@login_required
def count_notifs(request):
    from django.http import JsonResponse
    from apps.notifications.models import Notification
    n = Notification.objects.filter(destinataire=request.user, lue=False).count()
    return JsonResponse({'count': n})

@login_required
def notifications_view(request):
    from apps.notifications.models import Notification
    notifs = Notification.objects.filter(destinataire=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'notifications/liste.html', {'notifications': notifs})
