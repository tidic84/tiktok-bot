# 🎯 Guide - Sélection Intelligente des Vidéos

## 📝 Vue d'ensemble

Le bot utilise maintenant un système de **sélection intelligente** qui choisit automatiquement la meilleure vidéo à publier parmi toutes celles récupérées des créateurs.

## 🎯 Comment ça Fonctionne

### 1. Récupération des Vidéos

Le bot récupère toutes les vidéos des créateurs configurés (ex: 10 vidéos × 6 créateurs = 60 vidéos).

### 2. Filtrage par Qualité

Les vidéos sont filtrées selon les critères :
- ✅ Nombre minimum de likes (`MIN_LIKES`)
- ✅ Nombre minimum de vues (`MIN_VIEWS`)
- ✅ Taux d'engagement minimum (`MIN_ENGAGEMENT_RATE`)

### 3. Calcul du Score

Pour chaque vidéo, un **score de viralité** est calculé :

```python
score = (taux_engagement × 100) + (likes / 10000) + (shares / 1000)
```

Où le **taux d'engagement** est :

```python
taux_engagement = (likes + commentaires + partages) / vues
```

### 4. Tri par Score

Les vidéos sont triées par score décroissant (meilleure en premier).

### 5. Sélection Aléatoire

Le bot sélectionne **aléatoirement** une vidéo parmi les **N meilleures** (par défaut N=10).

**Pourquoi aléatoire ?**
- ✅ Évite de toujours prendre la vidéo #1 (diversité)
- ✅ Permet de republier des vidéos différentes à chaque cycle
- ✅ Plus naturel et moins prévisible

### 6. Enregistrement Intelligent

- **Vidéos UPLOADÉES** : Enregistrées dans la DB et **ne seront jamais republiées**
- **Vidéos NON uploadées** : Peuvent être **retraitées au prochain cycle**

## 🔄 Cycle de Vie d'une Vidéo

```
1. Récupération ──> 2. Filtrage ──> 3. Scoring ──> 4. Sélection aléatoire
                                                            │
                                                            ▼
                                                    5. Téléchargement
                                                            │
                                                            ▼
                                            ┌───────────────┴───────────────┐
                                            │                               │
                                      Upload réussi                  Upload échoué
                                            │                               │
                                            ▼                               ▼
                              Marquée comme UPLOADÉE          Reste en attente (DB)
                              (ne sera plus republiée)        (peut être retraitée)
```

## ⚙️ Configuration

### Dans `config.py`

```python
# Sélection intelligente des vidéos
SMART_SELECTION = True  # Activer la sélection intelligente
TOP_N_SELECTION = 10    # Sélectionner aléatoirement parmi les N meilleures
CLEANUP_PENDING_VIDEOS_DAYS = 7  # Supprimer les vidéos en attente après N jours
```

### Options Disponibles

#### `SMART_SELECTION`

- **True** (recommandé) : 1 seule vidéo sélectionnée intelligemment par cycle
- **False** : Ancienne méthode (plusieurs vidéos par cycle)

#### `TOP_N_SELECTION`

Nombre de meilleures vidéos parmi lesquelles choisir aléatoirement.

- **Valeur basse (3-5)** : Sélection plus restrictive (meilleures vidéos uniquement)
- **Valeur moyenne (10-15)** : Équilibre entre qualité et diversité (recommandé)
- **Valeur haute (20-30)** : Plus de diversité, qualité potentiellement moindre

#### `CLEANUP_PENDING_VIDEOS_DAYS`

Nombre de jours après lequel les vidéos en attente (non uploadées) sont supprimées de la DB.

- **Valeur basse (3-5 jours)** : Nettoyage fréquent
- **Valeur moyenne (7 jours)** : Recommandé
- **Valeur haute (14+ jours)** : Permet plus de retentatives

## 📊 Exemples de Scores

### Vidéo Très Virale

```
Vues        : 2,500,000
Likes       : 350,000
Commentaires: 8,000
Partages    : 15,000

Taux d'engagement = (350000 + 8000 + 15000) / 2500000 = 14.92%
Score = (0.1492 × 100) + (350000 / 10000) + (15000 / 1000)
Score = 14.92 + 35 + 15 = 64.92 ⭐⭐⭐⭐⭐
```

### Vidéo Moyennement Virale

```
Vues        : 500,000
Likes       : 45,000
Commentaires: 1,200
Partages    : 2,000

Taux d'engagement = (45000 + 1200 + 2000) / 500000 = 9.64%
Score = (0.0964 × 100) + (45000 / 10000) + (2000 / 1000)
Score = 9.64 + 4.5 + 2 = 16.14 ⭐⭐⭐
```

### Vidéo Peu Virale

```
Vues        : 100,000
Likes       : 5,000
Commentaires: 200
Partages    : 150

Taux d'engagement = (5000 + 200 + 150) / 100000 = 5.35%
Score = (0.0535 × 100) + (5000 / 10000) + (150 / 1000)
Score = 5.35 + 0.5 + 0.15 = 6.0 ⭐
```

## 🎲 Exemple de Sélection

Supposons que le bot récupère 60 vidéos avec les scores suivants :

```
Top 10 vidéos:
1. Vidéo A - Score: 72.5
2. Vidéo B - Score: 68.3
3. Vidéo C - Score: 65.1
4. Vidéo D - Score: 62.8
5. Vidéo E - Score: 60.2
6. Vidéo F - Score: 58.9
7. Vidéo G - Score: 57.4
8. Vidéo H - Score: 55.1
9. Vidéo I - Score: 53.7
10. Vidéo J - Score: 52.3
```

Avec `TOP_N_SELECTION = 10`, le bot choisira **aléatoirement** une vidéo parmi A, B, C, D, E, F, G, H, I, J.

**Probabilité** : Chaque vidéo du top 10 a 10% de chance d'être sélectionnée.

## 🔍 Logs du Bot

### Sélection Réussie

```
--- Phase 2: Sélection de la vidéo ---
🎲 Vidéo sélectionnée aléatoirement parmi les 10 meilleures:
   7123456789 - aflavorfulbite - 2,345,678 vues, 125,430 likes,
   engagement: 5.35%, score: 18.54
✓ 1 vidéo sélectionnée intelligemment (parmi top 10)
```

### Upload Réussi

```
✓ Vidéo 7123456789 uploadée avec succès (1/10)
```

La vidéo est marquée comme `is_uploaded = True` et ne sera **jamais republiée**.

### Upload Échoué

```
⊗ Échec de l'upload de 7123456789
```

La vidéo reste dans la DB avec `is_uploaded = False` et peut être **retraitée au prochain cycle**.

## 📈 Avantages de ce Système

### 1. Qualité Maximale

- ✅ Seules les vidéos les plus virales sont sélectionnées
- ✅ Score calculé scientifiquement
- ✅ Engagement réel privilégié

### 2. Diversité

- ✅ Sélection aléatoire parmi les meilleures (pas toujours la même)
- ✅ Différentes vidéos à chaque cycle
- ✅ Moins prévisible

### 3. Efficacité

- ✅ 1 seule vidéo uploadée par cycle (plus rapide)
- ✅ Moins de bande passante utilisée
- ✅ Moins de risque de détection

### 4. Retraitement Intelligent

- ✅ Vidéos non uploadées peuvent être retentées
- ✅ Pas de perte de contenu de qualité
- ✅ Nettoyage automatique des anciennes

## 🛠️ Personnalisation

### Exemple 1 : Sélection Ultra-Restrictive

```python
# Dans config.py
SMART_SELECTION = True
TOP_N_SELECTION = 3  # Seulement le top 3
MIN_LIKES = 100000   # Critères très élevés
MIN_VIEWS = 1000000
MIN_ENGAGEMENT_RATE = 0.10  # 10%
```

**Résultat** : Vidéos extrêmement virales uniquement.

### Exemple 2 : Sélection Équilibrée (Recommandé)

```python
# Dans config.py
SMART_SELECTION = True
TOP_N_SELECTION = 10  # Top 10
MIN_LIKES = 10000
MIN_VIEWS = 100000
MIN_ENGAGEMENT_RATE = 0.05  # 5%
```

**Résultat** : Bon équilibre entre qualité et quantité.

### Exemple 3 : Sélection Large

```python
# Dans config.py
SMART_SELECTION = True
TOP_N_SELECTION = 20  # Top 20
MIN_LIKES = 5000
MIN_VIEWS = 50000
MIN_ENGAGEMENT_RATE = 0.03  # 3%
```

**Résultat** : Plus de diversité, qualité potentiellement moindre.

## 🔄 Désactiver la Sélection Intelligente

Si vous préférez l'ancienne méthode (plusieurs vidéos par cycle) :

```python
# Dans config.py
SMART_SELECTION = False
```

Le bot reviendra au comportement original.

## 💡 Conseils d'Utilisation

### 1. Laissez le Système Fonctionner

La sélection intelligente est conçue pour fonctionner sur plusieurs cycles. Ne vous inquiétez pas si une vidéo "moins bonne" est sélectionnée occasionnellement.

### 2. Ajustez Progressivement

Commencez avec les valeurs par défaut, puis ajustez selon vos résultats :
- Trop de vidéos rejetées → Baissez les critères
- Qualité insuffisante → Augmentez les critères

### 3. Surveillez les Logs

Les logs vous indiquent toujours :
- Score de la vidéo sélectionnée
- Engagement réel
- Nombre de vidéos candidates

### 4. Nettoyage Régulier

Le bot nettoie automatiquement les vidéos en attente trop anciennes. Ajustez `CLEANUP_PENDING_VIDEOS_DAYS` selon vos besoins.

## 📊 Statistiques en Temps Réel

### Vidéos en Attente

Pour voir combien de vidéos sont en attente :

```python
from database.db_manager import DatabaseManager
from config import Config

config = Config()
db = DatabaseManager(config.DATABASE_URL)
pending = db.get_pending_videos()
print(f"{len(pending)} vidéos en attente")
```

### Vidéos Uploadées

```python
uploaded_today = db.get_uploaded_count_today()
print(f"{uploaded_today} vidéos uploadées aujourd'hui")
```

## 🎉 Conclusion

La sélection intelligente garantit que **seules les meilleures vidéos** sont uploadées, tout en permettant :
- ✅ De la diversité (sélection aléatoire)
- ✅ Des retentatives (retraitement possible)
- ✅ Un nettoyage automatique
- ✅ Une qualité maximale

**Bon botting avec la sélection intelligente ! 🚀**

