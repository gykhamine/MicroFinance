from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from apps.accounts.decorators import directeur_only, staff_only
import json

@login_required
@directeur_only
def tableau_bord(request):
    from apps.clients.models import Client
    from apps.comptes.models import Compte
    from apps.transactions.models import Transaction
    from apps.credits.models import DemandeCredit, Echeance
    from apps.cartes_31.models import Carte31
    from django.db.models import Sum
    from datetime import date, timedelta

    today = date.today()
    last_30 = today - timedelta(days=30)

    txns_mois = Transaction.objects.filter(date__date__gte=last_30)
    depots_mois = txns_mois.filter(type_transaction__in=['depot','carte_depot']).aggregate(s=Sum('montant'))['s'] or 0
    retraits_mois = txns_mois.filter(type_transaction='retrait').aggregate(s=Sum('montant'))['s'] or 0
    frais_mois = txns_mois.aggregate(s=Sum('frais'))['s'] or 0

    # Évolution quotidienne
    daily = {}
    for t in txns_mois.filter(type_transaction='depot'):
        d = str(t.date.date())
        daily[d] = float(daily.get(d, 0)) + float(t.montant)

    # Répartition types transactions
    type_counts = {}
    for t in txns_mois:
        label = t.get_type_transaction_display()
        type_counts[label] = type_counts.get(label, 0) + 1

    # Encours crédit par type
    encours = {}
    for c in DemandeCredit.objects.filter(statut='decaissee').select_related('type_credit'):
        k = c.type_credit.nom
        encours[k] = float(encours.get(k, 0)) + float(c.montant_accorde or 0)

    stats = {
        'nb_clients': Client.objects.filter(statut='actif').count(),
        'nb_comptes': Compte.objects.filter(actif=True).count(),
        'total_epargne': float(Compte.objects.filter(actif=True).aggregate(s=Sum('solde'))['s'] or 0),
        'credits_en_cours': DemandeCredit.objects.filter(statut='decaissee').count(),
        'encours_credit': float(DemandeCredit.objects.filter(statut='decaissee').aggregate(s=Sum('montant_accorde'))['s'] or 0),
        'echeances_retard': Echeance.objects.filter(statut='en_retard').count(),
        'cartes_actives': Carte31.objects.filter(statut__in=['active','complete']).count(),
        'cartes_cloturees': Carte31.objects.filter(statut='cloturee').count(),
        'depots_mois': float(depots_mois),
        'retraits_mois': float(retraits_mois),
        'frais_mois': float(frais_mois),
        'txns_mois': txns_mois.count(),
    }
    ctx = {
        'stats': stats,
        'daily_data': json.dumps(dict(sorted(daily.items()))),
        'type_counts': json.dumps(type_counts),
        'encours_credit': json.dumps(encours),
    }
    return render(request, 'rapports/tableau_bord.html', ctx)

@login_required
@directeur_only
def rapport_credits(request):
    from apps.credits.models import DemandeCredit, Echeance
    from django.db.models import Sum
    credits = DemandeCredit.objects.select_related('client__utilisateur','type_credit').all()
    statut = request.GET.get('statut','')
    if statut: credits = credits.filter(statut=statut)
    total_accorde = credits.filter(statut__in=['decaissee','cloturee']).aggregate(s=Sum('montant_accorde'))['s'] or 0
    total_retard = Echeance.objects.filter(statut='en_retard').aggregate(s=Sum('montant_total'))['s'] or 0
    return render(request, 'rapports/credits.html', {
        'credits': credits[:50], 'total_accorde': total_accorde, 'total_retard': total_retard, 'statut_filtre': statut
    })

@login_required
@directeur_only
def rapport_cartes(request):
    from apps.cartes_31.models import Carte31
    from django.db.models import Sum
    cartes = Carte31.objects.select_related('client__utilisateur').all()
    total_retenu = sum(c.montant_case_31 for c in cartes.filter(statut='cloturee') if c.montant_case_31) or 0
    return render(request, 'rapports/cartes.html', {'cartes': cartes[:50], 'total_retenu': total_retenu})

@login_required
@directeur_only
def exporter_pdf(request, type_r):
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from datetime import date
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    c.setFillColorRGB(0.05, 0.32, 0.58)
    c.rect(0, h-80, w, 80, fill=1, stroke=0)
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, h-45, "MicroFinance ERP — Rapport")
    c.setFont("Helvetica", 12)
    c.drawString(40, h-65, f"Généré le {date.today().strftime('%d/%m/%Y')}")
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 15)
    titres = {'transactions':'Journal des transactions','credits':'État des crédits','cartes':'Rapport Cartes 31'}
    c.drawString(40, h-110, titres.get(type_r,'Rapport'))
    y = h - 145
    c.setFont("Helvetica", 10)
    if type_r == 'transactions':
        from apps.transactions.models import Transaction
        for t in Transaction.objects.all()[:40]:
            if y < 70: c.showPage(); y = h-60
            c.drawString(40, y, f"  {t.date.strftime('%d/%m/%Y %H:%M')}  {t.reference}  {t.get_type_transaction_display()}  {t.montant:,.0f} FCFA")
            y -= 16
    elif type_r == 'credits':
        from apps.credits.models import DemandeCredit
        for cr in DemandeCredit.objects.all()[:40]:
            if y < 70: c.showPage(); y = h-60
            c.drawString(40, y, f"  {cr.client}  {cr.type_credit}  {cr.montant_demande:,.0f} FCFA  {cr.get_statut_display()}")
            y -= 16
    elif type_r == 'cartes':
        from apps.cartes_31.models import Carte31
        for carte in Carte31.objects.all()[:40]:
            if y < 70: c.showPage(); y = h-60
            c.drawString(40, y, f"  {carte.numero}  {carte.client}  {carte.cases_remplies}/31  {carte.get_statut_display()}")
            y -= 16
    c.save()
    buf.seek(0)
    resp = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="rapport_{type_r}.pdf"'
    return resp
