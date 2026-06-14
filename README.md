# MicroFinance ERP — Django
**by Gykhamine Concept Investigation**

## Démarrage

```bash
cd microfinance_erp
python manage.py runserver
# → http://127.0.0.1:8000/
```

## Comptes de démonstration

| Rôle | Login | Mot de passe | Accès |
|------|-------|-------------|-------|
| 👑 Directeur | `directeur` | `dir123` | Tout + rapports + configuration |
| 🏦 Agent bancaire | `banque1` | `banque123` | Caisse + instruction crédits |
| 💵 Caissier | `caissier1` | `caisse123` | Dépôts, retraits, transferts, cartes 31 |
| 📋 Agent crédit | `preteur1` | `pret123` | Instruction + décaissement crédits |
| 👤 Client | `jean.mabiala` | `client123` | Espace personnel |
| 👤 Client | `fatou.diallo` | `client123` | Espace personnel (carte 31 active) |

## Deux modes de fonctionnement

### 🏦 Mode Bancaire classique
- Ouverture et gestion de comptes (Courant, Épargne, Enfant)
- Dépôts, retraits, transferts internes (entre clients de la MF)
- Crédits avec tableau d'amortissement mensuel
- Plans d'épargne programmés
- Taxes et frais configurables par le directeur

### 🃏 Mode Carte 31 (produit spécial)
- Le client achète une carte avec **31 cases**
- Il remplit les cases à son rythme, avec le **montant de son choix** par case
- À la clôture : la case au **montant le plus élevé revient à la microfinance** (case 31)
- Le client récupère la somme des **30 autres cases**
- Exemple : 30 cases × 5 000 FCFA + 1 case à 8 000 FCFA
  → Client reçoit 150 000 FCFA | MF retient 8 000 FCFA

## Modules

| Module | Fonctionnalités |
|--------|----------------|
| `clients` | Enregistrement KYC, numéro client, QR code |
| `comptes` | Ouverture, types configurables, solde temps réel |
| `transactions` | Dépôt, retrait, transfert interne, journal complet |
| `cartes_31` | Grille 31 cases, dépôt par case, clôture automatique |
| `credits` | Demande → instruction → approbation → décaissement → amortissement → remboursement |
| `epargne` | Plans d'épargne avec versements progressifs |
| `rapports` | Dashboard Chart.js, PDF ReportLab, état crédits, état cartes |
| `notifications` | WebSocket temps réel + toasts |

## Séparation des droits

| Action | Directeur | Agent Bancaire | Caissier | Agent Crédit | Client |
|--------|:---------:|:--------------:|:--------:|:------------:|:------:|
| Dépôt / Retrait / Transfert | ✅ | ✅ | ✅ | — | — |
| Carte 31 (créer, déposer, clôturer) | ✅ | ✅ | ✅ | — | 👁️ |
| Crédit (demande) | ✅ | ✅ | ✅ | ✅ | — |
| Crédit (instruire + décaisser) | ✅ | ✅ | — | ✅ | — |
| Remboursement échéances | ✅ | ✅ | ✅ | — | — |
| Configuration taxes | ✅ | — | — | — | — |
| Rapports complets | ✅ | — | — | — | — |
| Créer utilisateurs | ✅ | — | — | — | — |

## Données démo incluses
- 4 clients avec comptes courants ouverts
- Carte 31 partielle (12/31 cases) — `fatou.diallo`
- Carte 31 complète (31/31) prête à clôturer — `alain.bitsindou`
- Crédit décaissé de 200 000 FCFA / 6 mois avec tableau amortissement — `jean.mabiala`
- Plan d'épargne actif — `nadege.nganga`
- 3 taxes configurées (retrait 0.5%, transfert 1%, carte 31 désactivée)
