# 🍪 Guide - Import de Cookies JSON

## 📝 Vue d'ensemble

Le bot supporte maintenant l'import de cookies TikTok depuis un fichier JSON, ce qui facilite grandement la connexion sans avoir à se connecter manuellement à chaque fois.

## 🎯 Avantages

- ✅ **Plus rapide** : Pas besoin de connexion manuelle
- ✅ **Plus fiable** : Les cookies sont déjà valides
- ✅ **Portable** : Exportez vos cookies depuis n'importe quel navigateur
- ✅ **Backup automatique** : Les cookies sont sauvegardés en pickle ET JSON

## 📥 Comment Exporter vos Cookies

### Méthode 1 : Extension de Navigateur (Recommandé)

#### Chrome / Edge / Brave

1. Installez l'extension **"Cookie-Editor"** ou **"EditThisCookie"**
2. Allez sur `https://www.tiktok.com` et connectez-vous
3. Cliquez sur l'icône de l'extension
4. Cliquez sur "Export" → "JSON"
5. Sauvegardez le fichier (ex: `tiktok_cookies.json`)

#### Firefox

1. Installez l'extension **"Cookie Quick Manager"**
2. Allez sur `https://www.tiktok.com` et connectez-vous
3. Ouvrez l'extension
4. Sélectionnez tous les cookies TikTok
5. Exportez en JSON

### Méthode 2 : Console Développeur

1. Allez sur `https://www.tiktok.com` et connectez-vous
2. Ouvrez la console développeur (F12)
3. Allez dans l'onglet "Application" (Chrome) ou "Stockage" (Firefox)
4. Cliquez sur "Cookies" → "https://www.tiktok.com"
5. Copiez manuellement les cookies importants (voir liste ci-dessous)

### Cookies Importants

Les cookies essentiels pour TikTok sont :
- `sessionid` ou `sessionid_ss` ⭐ **CRITIQUE**
- `sid_tt` ⭐ **CRITIQUE**
- `sid_guard` ⭐ **CRITIQUE**
- `ssid_ucp_v1`
- `sid_ucp_v1`
- `ttwid`
- `msToken`
- `tt_csrf_token`

## 📤 Import des Cookies

### Étape 1 : Placer le Fichier JSON

Placez votre fichier JSON dans le dossier du projet :

```bash
/home/tidic/Documents/Dev/Tiktok/tiktok_cookies.json
```

### Étape 2 : Importer les Cookies

Utilisez le script d'import fourni :

```bash
python import_cookies.py tiktok_cookies.json
```

ou simplement (si le fichier s'appelle `tiktok_cookies.json`) :

```bash
python import_cookies.py
```

### Étape 3 : Vérification

Le script affichera :

```
============================================================
IMPORT DE COOKIES TIKTOK DEPUIS JSON
============================================================
Fichier JSON: tiktok_cookies.json

Import des cookies depuis tiktok_cookies.json...
✓ 35 cookies chargés depuis tiktok_cookies.json
✓ 35 cookies sauvegardés dans tiktok_cookies.pkl
✓ 35 cookies sauvegardés dans tiktok_cookies.json

============================================================
✅ IMPORT RÉUSSI !
============================================================

Les cookies ont été importés et sauvegardés dans:
  • tiktok_cookies.pkl (pickle)
  • tiktok_cookies.json (JSON backup)

Vous pouvez maintenant lancer le bot:
  python main.py

Le bot utilisera automatiquement ces cookies pour se connecter.
```

## 🚀 Utilisation

Une fois les cookies importés, lancez simplement le bot :

```bash
python main.py
```

Le bot chargera automatiquement les cookies et se connectera sans intervention manuelle !

## 📊 Format JSON Supporté

Le bot supporte le format JSON standard exporté par les extensions de navigateur :

```json
[
    {
        "name": "sessionid",
        "value": "4896eb5e1795bd6867fbef8107f00c7d",
        "domain": ".tiktok.com",
        "path": "/",
        "secure": true,
        "httpOnly": true,
        "sameSite": null,
        "expirationDate": 1777910179.002
    },
    ...
]
```

### Champs Supportés

- `name` ⭐ **REQUIS**
- `value` ⭐ **REQUIS**
- `domain` ⭐ **REQUIS**
- `path` (optionnel, défaut: "/")
- `secure` (optionnel)
- `httpOnly` (optionnel)
- `sameSite` (optionnel)
- `expirationDate` (optionnel, converti en `expiry`)

## 🔄 Conversion Automatique

Le bot convertit automatiquement le format JSON vers le format Selenium :

- `expirationDate` → `expiry` (converti en entier)
- `sameSite: "no_restriction"` → `sameSite: "None"`
- Autres champs copiés tels quels

## 🛠️ Dépannage

### Problème : "Aucun cookie valide trouvé"

**Causes possibles** :
- Le fichier JSON est mal formaté
- Les cookies sont expirés
- Le format n'est pas reconnu

**Solution** :
1. Vérifiez que le JSON est valide (utilisez un validateur JSON en ligne)
2. Assurez-vous d'avoir les cookies `sessionid`, `sid_tt`, et `sid_guard`
3. Exportez à nouveau les cookies depuis votre navigateur

### Problème : "Connexion échouée malgré les cookies"

**Causes possibles** :
- Les cookies ont expiré
- TikTok a détecté une activité suspecte
- L'IP a changé

**Solution** :
1. Reconnectez-vous manuellement sur TikTok dans votre navigateur
2. Exportez à nouveau les cookies
3. Réimportez-les avec `python import_cookies.py`

### Problème : "Impossible d'ajouter le cookie X"

**Cause** : Certains cookies ne peuvent pas être ajoutés par Selenium (normal)

**Solution** : Aucune action nécessaire, le bot ajoute les cookies compatibles

## 💡 Conseils

### 1. Cookies Frais

Exportez vos cookies juste après vous être connecté pour avoir les cookies les plus frais possible.

### 2. Backup Automatique

Le bot sauvegarde automatiquement les cookies en JSON lors de la connexion manuelle, vous pouvez donc les réutiliser plus tard.

### 3. Renouvellement

Si les cookies expirent, reconnectez-vous manuellement une fois, le bot sauvegardera automatiquement les nouveaux cookies.

### 4. Sécurité

⚠️ **IMPORTANT** : Ne partagez JAMAIS vos cookies ! Ils donnent accès complet à votre compte TikTok.

Ajoutez `tiktok_cookies.json` à votre `.gitignore` :

```bash
echo "tiktok_cookies.json" >> .gitignore
echo "*.json" >> .gitignore  # Ou plus large
```

## 📁 Fichiers Générés

Après l'import, vous aurez :

```
/home/tidic/Documents/Dev/Tiktok/
├── tiktok_cookies.pkl      # Format pickle (utilisé par le bot)
├── tiktok_cookies.json     # Backup JSON (pour réimport facile)
└── tiktok_cookies.json     # Votre fichier original (peut être supprimé)
```

## 🔄 Workflow Recommandé

1. **Première fois** :
   - Exportez vos cookies depuis le navigateur
   - Importez-les avec `python import_cookies.py`
   - Lancez le bot

2. **Utilisation quotidienne** :
   - Lancez simplement le bot
   - Les cookies sont chargés automatiquement

3. **Si les cookies expirent** :
   - Connectez-vous manuellement (le bot vous le demandera)
   - Les nouveaux cookies sont sauvegardés automatiquement
   - Ou réexportez depuis le navigateur et réimportez

## 📚 Voir Aussi

- `uploader/cookie_manager.py` - Code source du gestionnaire de cookies
- `import_cookies.py` - Script d'import
- `README.md` - Documentation générale

## ❓ Questions Fréquentes

### Q : Combien de temps les cookies sont-ils valides ?

**R** : Généralement 1-2 semaines, mais cela dépend de TikTok. Le bot vous avertira si les cookies sont expirés.

### Q : Puis-je utiliser les cookies d'un autre navigateur ?

**R** : Oui ! Exportez simplement les cookies depuis n'importe quel navigateur et importez-les.

### Q : Les cookies fonctionnent-ils sur plusieurs machines ?

**R** : Oui, mais TikTok peut détecter le changement d'IP. Utilisez un VPN si nécessaire.

### Q : Que faire si j'ai plusieurs comptes TikTok ?

**R** : Créez un fichier JSON par compte (ex: `account1_cookies.json`, `account2_cookies.json`) et importez celui que vous voulez utiliser.

## 🎉 Conclusion

L'import de cookies JSON simplifie grandement l'utilisation du bot en évitant la connexion manuelle à chaque démarrage. Exportez vos cookies une fois et profitez d'une connexion automatique !

**Bon botting ! 🚀**

