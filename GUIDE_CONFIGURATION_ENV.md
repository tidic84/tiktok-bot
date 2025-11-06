# ⚙️ Guide - Configuration via .env

## 📝 Vue d'ensemble

Le bot supporte maintenant la configuration des créateurs TikTok via un fichier `.env`, ce qui permet de personnaliser facilement les créateurs à suivre sans modifier le code.

## 🎯 Avantages

- ✅ **Facile à modifier** : Changez les créateurs sans toucher au code
- ✅ **Portable** : Partagez votre configuration facilement
- ✅ **Sécurisé** : Gardez vos identifiants séparés du code
- ✅ **Flexible** : Ajoutez autant de créateurs que vous voulez

## 🚀 Configuration

### Étape 1 : Créer le Fichier .env

Copiez le fichier exemple :

```bash
cp env.example .env
```

Ou créez manuellement un fichier `.env` à la racine du projet.

### Étape 2 : Éditer le Fichier

Ouvrez `.env` dans votre éditeur de texte :

```bash
nano .env
# ou
vim .env
# ou
code .env  # VS Code
```

### Étape 3 : Configurer les Créateurs

Ajoutez vos créateurs TikTok (séparés par des virgules) :

```env
# Identifiants TikTok
TIKTOK_USERNAME=votre_username
TIKTOK_PASSWORD=votre_mot_de_passe

# Créateurs à suivre (séparés par des virgules, sans espaces)
TARGET_CREATORS=aflavorfulbite,joandbart,feelgoodfoodie,cookingwithshereen
```

## 📋 Exemples par Niche

### Food / Recipes

```env
TARGET_CREATORS=aflavorfulbite,joandbart,feelgoodfoodie,cookingwithshereen,freshfitfood_,malcomsfood2
```

### Gaming

```env
TARGET_CREATORS=ninja,pokimane,tfue,shroud,valkyrae,sykkuno
```

### Fitness

```env
TARGET_CREATORS=chloe_t,blogilates,kayla_itsines,whitneyysimmons,pamela_rf
```

### DIY / Crafts

```env
TARGET_CREATORS=5minutecrafts,diyqueen,craftsbymeghan,troom_troom,craftfactory
```

### Fashion

```env
TARGET_CREATORS=charlidamelio,addisonre,avani,dixiedamelio,lorengray
```

### Comedy

```env
TARGET_CREATORS=zachking,brittany_broski,spencerx,daviddobrik,larray
```

### Beauty / Makeup

```env
TARGET_CREATORS=jamescharles,nikkietutorials,jeffreestar,manny_mua,jackieaina
```

### Travel

```env
TARGET_CREATORS=drewbinsky,kara_and_nate,samuel_and_audrey,vagabrothers,lostleblanc
```

## 🔍 Comment Trouver des Créateurs

### 1. Recherche TikTok

1. Allez sur TikTok
2. Recherchez votre niche (ex: "recipes", "fitness", "gaming")
3. Regardez les créateurs populaires
4. Notez leurs noms d'utilisateur (sans le @)

### 2. Outils de Recherche

- **TikTok Analytics** : Trouvez les créateurs les plus populaires
- **Social Blade** : Statistiques des créateurs
- **Google** : "top tiktok creators [votre niche]"

### 3. Critères de Sélection

Choisissez des créateurs avec :
- ✅ Beaucoup d'abonnés (100K+)
- ✅ Bon taux d'engagement
- ✅ Publications régulières
- ✅ Contenu viral
- ✅ Dans votre niche

## ⚙️ Format du Fichier .env

### Règles Importantes

1. **Pas d'espaces** autour des virgules
   ```env
   # ✅ BON
   TARGET_CREATORS=creator1,creator2,creator3
   
   # ❌ MAUVAIS
   TARGET_CREATORS=creator1, creator2, creator3
   ```

2. **Pas de @** devant les noms
   ```env
   # ✅ BON
   TARGET_CREATORS=aflavorfulbite,joandbart
   
   # ❌ MAUVAIS
   TARGET_CREATORS=@aflavorfulbite,@joandbart
   ```

3. **Pas de guillemets** nécessaires
   ```env
   # ✅ BON
   TARGET_CREATORS=creator1,creator2
   
   # ❌ INUTILE (mais fonctionne)
   TARGET_CREATORS="creator1,creator2"
   ```

4. **Une ligne** pour tous les créateurs
   ```env
   # ✅ BON
   TARGET_CREATORS=creator1,creator2,creator3,creator4
   
   # ❌ MAUVAIS (ne fonctionne pas)
   TARGET_CREATORS=creator1,creator2
   TARGET_CREATORS=creator3,creator4
   ```

## 🔄 Fallback Automatique

Si vous ne configurez pas `TARGET_CREATORS` dans `.env`, le bot utilisera les créateurs par défaut définis dans `config.py` :

```python
TARGET_CREATORS = [
    'aflavorfulbite',
    'joandbart',
    'feelgoodfoodie',
    'cookingwithshereen',
    'freshfitfood_',
    'malcomsfood2'
]
```

## 🧪 Tester la Configuration

Vérifiez que vos créateurs sont bien chargés :

```bash
python -c "from config import Config; c = Config(); print('Créateurs:', c.TARGET_CREATORS)"
```

Sortie attendue :

```
Créateurs: ['aflavorfulbite', 'joandbart', 'feelgoodfoodie', ...]
```

## 💡 Conseils

### 1. Nombre de Créateurs

- **Minimum** : 3-5 créateurs (pour avoir assez de contenu)
- **Optimal** : 10-15 créateurs (bon équilibre)
- **Maximum** : Pas de limite, mais plus = plus lent

### 2. Diversification

Mélangez différents types de créateurs dans votre niche :
- Gros créateurs (1M+ abonnés) : Contenu viral garanti
- Créateurs moyens (100K-1M) : Bon contenu, moins saturé
- Petits créateurs (10K-100K) : Contenu unique

### 3. Mise à Jour

Mettez à jour régulièrement votre liste :
- Ajoutez de nouveaux créateurs populaires
- Retirez ceux qui ne postent plus
- Testez différentes combinaisons

### 4. Niche Spécifique

Restez dans une niche pour :
- Meilleure cohérence de contenu
- Meilleur engagement
- Moins de risque de ban

## 🛠️ Dépannage

### Problème : "Aucune vidéo récupérée"

**Causes possibles** :
- Noms d'utilisateurs incorrects
- Créateurs privés ou supprimés
- Erreur de syntaxe dans .env

**Solution** :
1. Vérifiez les noms d'utilisateurs sur TikTok
2. Assurez-vous qu'il n'y a pas d'espaces
3. Testez avec un seul créateur d'abord

### Problème : "Le bot utilise les créateurs par défaut"

**Cause** : Le fichier .env n'est pas lu ou `TARGET_CREATORS` n'est pas défini

**Solution** :
1. Vérifiez que le fichier s'appelle bien `.env` (avec le point)
2. Vérifiez que `TARGET_CREATORS` est bien défini
3. Relancez le bot

### Problème : "Erreur de parsing"

**Cause** : Format incorrect dans .env

**Solution** :
```env
# ✅ Format correct
TARGET_CREATORS=creator1,creator2,creator3

# Pas de:
# - Espaces autour des virgules
# - Guillemets (sauf si nécessaire)
# - Retours à la ligne dans la valeur
```

## 📁 Structure des Fichiers

```
/home/tidic/Documents/Dev/Tiktok/
├── .env                    # Votre configuration (à créer)
├── env.example             # Fichier exemple (fourni)
├── config.py               # Lit les variables .env
└── ...
```

## 🔒 Sécurité

### Fichier .gitignore

Assurez-vous que `.env` est dans votre `.gitignore` :

```bash
echo ".env" >> .gitignore
```

### Ne Partagez Jamais

⚠️ **IMPORTANT** : Ne partagez JAMAIS votre fichier `.env` ! Il contient vos identifiants TikTok.

### Backup

Faites un backup de votre `.env` dans un endroit sûr (pas sur GitHub) :

```bash
cp .env .env.backup
```

## 📊 Exemple Complet

Voici un exemple complet de fichier `.env` :

```env
# ========================================
# IDENTIFIANTS TIKTOK
# ========================================
TIKTOK_USERNAME=mon_compte_bot
TIKTOK_PASSWORD=MonMotDePasseSecurise123!

# ========================================
# CRÉATEURS TIKTOK
# ========================================
# Food/Recipes (ma niche)
TARGET_CREATORS=aflavorfulbite,joandbart,feelgoodfoodie,cookingwithshereen,freshfitfood_,malcomsfood2,tasty,buzzfeedtasty,foodnetwork,gordonramsayofficial

# ========================================
# NOTES
# ========================================
# - 10 créateurs configurés
# - Mélange de gros et moyens créateurs
# - Tous dans la niche food/recipes
# - Mis à jour le 05/11/2025
```

## 🎉 Conclusion

La configuration via `.env` rend le bot beaucoup plus flexible et facile à personnaliser. Vous pouvez maintenant changer de niche ou de créateurs en quelques secondes !

**Bon botting ! 🚀**

