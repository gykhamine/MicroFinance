from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Client
from apps.accounts.models import Utilisateur
from apps.accounts.decorators import staff_only, directeur_only, caissier_only

@login_required
@staff_only
def liste_clients(request):
    q = request.GET.get('q','')
    clients = Client.objects.select_related('utilisateur').filter(statut='actif')
    if q:
        clients = clients.filter(
            Q(utilisateur__first_name__icontains=q)|Q(utilisateur__last_name__icontains=q)|
            Q(numero_client__icontains=q)|Q(utilisateur__telephone__icontains=q)
        )
    return render(request, 'clients/liste.html', {'clients': clients, 'q': q})

@login_required
def detail_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.user.role == 'client':
        try:
            if request.user.profil_client.pk != pk:
                return redirect('dashboard')
        except: return redirect('dashboard')
    from apps.transactions.models import Transaction
    from apps.credits.models import DemandeCredit, Echeance
    from apps.cartes_31.models import Carte31
    ctx = {
        'client': client,
        'comptes': client.comptes.filter(actif=True),
        'transactions': Transaction.objects.filter(compte__client=client).select_related('caissier')[:20],
        'cartes': Carte31.objects.filter(client=client)[:10],
        'credits': DemandeCredit.objects.filter(client=client)[:10],
        'echeances_retard': Echeance.objects.filter(demande__client=client, statut='en_retard'),
    }
    return render(request, 'clients/detail.html', ctx)

@login_required
@caissier_only
def creer_client(request):
    if request.method == 'POST':
        u = Utilisateur.objects.create_user(
            username=request.POST['username'],
            password=request.POST.get('password','client123'),
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=request.POST.get('email',''),
            telephone=request.POST.get('telephone',''),
            role='client',
        )
        c = Client.objects.create(
            utilisateur=u,
            date_naissance=request.POST.get('date_naissance') or None,
            lieu_naissance=request.POST.get('lieu_naissance',''),
            type_piece=request.POST.get('type_piece',''),
            numero_piece=request.POST.get('numero_piece',''),
            profession=request.POST.get('profession',''),
            revenu_mensuel=request.POST.get('revenu_mensuel') or 0,
            agent_ouverture=request.user,
            notes=request.POST.get('notes',''),
        )
        # Ouvrir automatiquement un compte courant
        from apps.comptes.models import TypeCompte, Compte
        type_courant = TypeCompte.objects.filter(code='CCO').first()
        if type_courant:
            Compte.objects.create(client=c, type_compte=type_courant, agent_ouverture=request.user)
        messages.success(request, f"Client {u.get_full_name()} enregistré. N° {c.numero_client}")
        return redirect('detail_client', pk=c.pk)
    return render(request, 'clients/form.html')
