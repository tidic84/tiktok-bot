# 🚀 Guide Rapide - Bot TikTok

## Configuration en 3 étapes

### 1️⃣ Choisir vos créateurs

Ouvrez `config.py` et modifiez la liste des créateurs :

```python
# MODE RECOMMANDÉ: 'creators'
SCRAPING_MODE = 'creators'

# Vos créateurs TikTok (sans le @)
TARGET_CREATORS = [
    'gordonramsayofficial',
    'emmajanesfood',
    'feelgoodfoodie',
    # Ajoutez les vôtres ici
]

VIDEOS_PER_CREATOR = 5  # Nombre de vidéos par créateur
```

### 2️⃣ Ajuster les critères (optionnel)

```python
# Critères de sélection
MIN_LIKES = 5000        # Minimum de likes
MIN_VIEWS = 50000       # Minimum de vues
MIN_ENGAGEMENT_RATE = 0.03  # 3% d'engagement
```

### 3️⃣ Lancer le bot

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer
python main.py
```

## 🔍 Comment trouver des créateurs ?

1. Allez sur [tiktok.com](https://www.tiktok.com)
2. Cherchez votre thème : `#recipes`, `#fitness`, `#gaming`
3. Notez les noms d'utilisateurs (sans le @)
4. Ajoutez-les dans `TARGET_CREATORS`

## 📊 Exemples par niche

### 🍳 Food/Recipes
```python
TARGET_CREATORS = [
    'gordonramsayofficial',
    'emmajanesfood',
    'feelgoodfoodie',
    'cookingwithshereen',
    'twisted',
]
```

### 🎮 Gaming
```python
TARGET_CREATORS = [
    'gaming',
    'moistcr1tikal',
    'nickeh30',
    'tfue',
]
```

### 💪 Fitness
```python
TARGET_CREATORS = [
    'kayla_itsines',
    'blogilates',
    'alexisgaynor',
]
```

## ⚠️ Mode "search" (expérimental)

Si vous voulez essayer la recherche par mots-clés (peut ne pas fonctionner) :

```python
SCRAPING_MODE = 'search'

TARGET_KEYWORDS = ['recipes', 'food cooking', 'easy recipes']
VIDEOS_PER_KEYWORD = 10
```

**Note:** Ce mode ne fonctionne pas toujours. Le mode 'creators' est plus fiable !

## 🐛 Problèmes courants

**"0 vidéos récupérées"**
- Vérifiez que les noms sont corrects (sans @)
- Vérifiez que les profils sont publics
- Essayez d'autres créateurs

**Erreurs de timeout**
- Normal si vous utilisez le mode 'api'
- Passez au mode 'creators'

## 💡 Conseils

✅ Commencez avec 5 créateurs
✅ Utilisez le mode 'creators' (le plus fiable)
✅ Ajustez les critères selon vos besoins
✅ Surveillez les logs dans `logs/`

C'est tout ! 🎉

