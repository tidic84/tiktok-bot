# Configuration Instagram pour le Bot

Ce guide explique comment configurer l'authentification Instagram pour utiliser le scraper basé sur **instaloader**.

## Pourquoi instaloader ?

Le nouveau scraper Instagram utilise **instaloader** au lieu de Selenium, ce qui apporte :

✅ **Plus stable** : API Python mature au lieu de scraping HTML fragile
✅ **Plus simple** : Pas besoin de ChromeDriver ou de gestion de cookies JSON
✅ **Plus complet** : Métadonnées complètes (likes, vues, commentaires, caption, date)
✅ **Plus fiable** : Gestion automatique des rate limits et reprises
✅ **Plus léger** : Aucun navigateur requis pour Instagram

---

## Méthode 1 : Authentification avec username/password (Simple)

### 1. Créer un fichier `.env`

Copiez le fichier `.env.example` :

```bash
cp .env.example .env
```

### 2. Configurer vos identifiants

Éditez le fichier `.env` et remplissez :

```bash
INSTAGRAM_USERNAME=votre_username_instagram
INSTAGRAM_PASSWORD=votre_mot_de_passe_instagram
```

### 3. Tester

Lancez le bot :

```bash
python main.py
```

Le scraper se connectera automatiquement à Instagram et sauvegardera une session pour les prochaines fois.

---

## Méthode 2 : Session file (Plus sécurisé, RECOMMANDÉ)

Cette méthode évite de stocker votre mot de passe en clair et est plus sécurisée.

### 1. Installer instaloader

```bash
pip install instaloader
```

### 2. Se connecter à Instagram

```bash
instaloader -l votre_username_instagram
```

Instaloader vous demandera votre mot de passe et créera un fichier de session.

**Important** : Si Instagram demande une vérification à deux facteurs (2FA), suivez les instructions dans le terminal.

### 3. Configurer le fichier de session dans `config.py`

Ouvrez `config.py` et ajoutez :

```python
# Instagram session file (créé par instaloader -l)
INSTAGRAM_SESSION_FILE = "session-votre_username_instagram"
```

### 4. Configurer le username dans `.env`

Créez un fichier `.env` (si pas déjà fait) :

```bash
INSTAGRAM_USERNAME=votre_username_instagram
# Pas besoin de INSTAGRAM_PASSWORD avec une session file
```

### 5. Tester

Lancez le bot :

```bash
python main.py
```

Le scraper utilisera la session existante au lieu de se reconnecter.

---

## Méthode 3 : Sans authentification (Limité)

Si vous ne configurez pas d'authentification, le scraper fonctionnera **en mode limité** :

- ❌ Impossible d'accéder aux profils privés
- ❌ Rate limiting plus strict
- ❌ Moins de métadonnées disponibles
- ⚠️ Peut échouer sur certains profils

**Cette méthode n'est pas recommandée** pour une utilisation en production.

---

## Vérifier la configuration

Pour vérifier que tout fonctionne, lancez le bot avec un seul créateur :

1. Dans `config.py`, configurez :

```python
SOURCE_PLATFORM = 'instagram'
SCRAPING_MODE = 'creators'
INSTAGRAM_CREATORS = ['natgeo']  # Profil de test (National Geographic)
```

2. Lancez le bot :

```bash
python main.py
```

3. Vérifiez les logs. Vous devriez voir :

```
✓ Session Instagram chargée avec succès
📥 Récupération depuis 1 créateur(s) Instagram...
Récupération des vidéos Instagram de @natgeo...
✓ X vidéos Instagram récupérées de @natgeo
```

---

## Configuration des délais (Rate Limiting)

Pour éviter le rate limiting Instagram, le scraper attend **30-60 secondes** entre chaque créateur par défaut.

Vous pouvez configurer ces délais dans `config.py` :

```python
# Délais entre les créateurs Instagram (en secondes)
INSTAGRAM_MIN_DELAY_BETWEEN_CREATORS = 30  # Minimum
INSTAGRAM_MAX_DELAY_BETWEEN_CREATORS = 60  # Maximum (aléatoire)
```

**⚠️ Important** : Ne réduisez pas ces délais, Instagram bannit les comptes qui font trop de requêtes !

### Recommandations :

- **1-3 créateurs** : Délais de 30-60 secondes (par défaut) ✅
- **4-9 créateurs** : Augmentez à 60-120 secondes 🔶
- **10+ créateurs** : Augmentez à 120-180 secondes ou divisez en plusieurs sessions 🔴

---

## Problèmes courants

### "LoginRequiredException"

➡️ **Solution** : Configurez l'authentification (Méthode 1 ou 2)

### "ProfileNotExistsException"

➡️ **Solution** : Vérifiez que le nom d'utilisateur est correct (sans @)

### "401 Unauthorized" ou "Please wait a few minutes"

**C'est le rate limiting Instagram !**

➡️ **Solutions** :
1. **Attendez 1-2 heures** avant de réessayer
2. **Réduisez le nombre de créateurs** à 1-2 pour tester
3. **Augmentez les délais** dans `config.py` (voir section ci-dessus)
4. **Utilisez un compte Instagram plus établi** (évitez les comptes neufs)

Le scraper **arrêtera automatiquement** le scraping si rate limité pour protéger votre compte.

### "QueryReturnedBadRequestException" ou "429 Too Many Requests"

➡️ **Solution** : Identique à l'erreur 401 ci-dessus. Instagram limite votre compte.

### "Profil privé et non suivi"

➡️ **Solution** : Vous devez suivre le profil privé avec votre compte Instagram, ou choisir des profils publics.

### Le scraper charge encore Selenium

➡️ **Solution** : Nettoyez le cache Python et relancez :

```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
python main.py
```

---

## Logs attendus

Avec le nouveau scraper, vous devriez voir des logs comme :

```
✓ Session Instagram chargée avec succès
Récupération des vidéos Instagram de @username...
✓ 10 vidéos Instagram récupérées de @username
📊 Total: 10 vidéos Instagram uniques de 1 créateurs
```

**Pas** de logs Selenium comme :
- ❌ "WebDriver manager"
- ❌ "Selenium Chrome initialisé"
- ❌ "Chargement des cookies depuis: instagram_cookies.json"

---

## Ressources

- Documentation instaloader : https://instaloader.github.io/
- Repository GitHub : https://github.com/instaloader/instaloader
- Exemples de code : https://instaloader.github.io/as-module.html

---

## Support

Si vous rencontrez des problèmes :

1. Vérifiez que `instaloader>=4.10` est installé : `pip list | grep instaloader`
2. Vérifiez que le cache Python est nettoyé (voir section "Problèmes courants")
3. Vérifiez vos identifiants Instagram
4. Consultez les logs pour identifier l'erreur exacte
