# 🔧 Résolution des Problèmes de Connexion TikTok

## 🔍 Diagnostiquer le problème

### Étape 1: Tester la connexion

Lancez le script de test :

```bash
source venv/bin/activate
python test_connexion.py
```

Ce script va :
- ✅ Initialiser le navigateur Chrome
- ✅ Charger les cookies existants
- ✅ Vérifier la connexion
- ✅ Tester l'accès à la page d'upload

### Étape 2: Comprendre les erreurs

#### Erreur: "Connection refused" ou "Max retries exceeded"

**Cause:** Le navigateur Chrome s'est fermé pendant l'exécution du bot.

**Solution:**
1. Vérifiez que Chrome est installé : `google-chrome --version`
2. Mettez `HEADLESS_MODE = False` dans `config.py` pour voir ce qui se passe
3. Le bot va maintenant se reconnecter automatiquement

#### Erreur: "Pas connecté à TikTok" ou "Connexion via cookies échouée"

**Cause:** Les cookies ont expiré ou sont invalides.

**Solution:**
1. Supprimez l'ancien fichier de cookies :
   ```bash
   rm tiktok_cookies.pkl
   ```

2. Relancez le bot - il vous demandera de vous connecter manuellement :
   ```bash
   python main.py
   ```

3. Une fenêtre Chrome s'ouvrira - **connectez-vous manuellement** à TikTok

4. Une fois connecté, le bot sauvegardera automatiquement les nouveaux cookies

#### Erreur: "Timeout: connexion non effectuée dans les temps"

**Cause:** Vous n'avez pas eu le temps de vous connecter (5 minutes max).

**Solution:**
1. Relancez le bot
2. Connectez-vous plus rapidement
3. Ou modifiez le timeout dans `uploader/selenium_uploader.py` ligne 144 :
   ```python
   max_wait = 600  # 10 minutes au lieu de 5
   ```

## 🔄 Procédure de reconnexion complète

Si rien ne fonctionne, voici la procédure complète :

```bash
# 1. Arrêtez le bot (Ctrl+C)

# 2. Supprimez les anciens cookies
rm tiktok_cookies.pkl

# 3. Vérifiez votre config
cat config.py | grep -E "HEADLESS_MODE|TIKTOK"

# 4. Assurez-vous que HEADLESS_MODE = False
# Pour voir le navigateur et se connecter manuellement

# 5. Relancez le bot
python main.py

# 6. Connectez-vous manuellement dans la fenêtre Chrome qui s'ouvre

# 7. Une fois connecté, le bot continue automatiquement
```

## 🔑 Vérifier les identifiants

Les identifiants sont dans le fichier `.env` :

```bash
# Voir (sans afficher les valeurs)
cat .env | grep TIKTOK | sed 's/=.*/=***/'
```

Pour modifier :
```bash
nano .env
```

Et ajoutez :
```
TIKTOK_USERNAME=votre_username
TIKTOK_PASSWORD=votre_password
```

**Note:** Les identifiants ne sont utilisés que si la connexion par cookies échoue.

## 🌐 Mode headless vs visible

### Mode visible (RECOMMANDÉ pour déboguer)

```python
# config.py
HEADLESS_MODE = False
```

- ✅ Vous voyez le navigateur
- ✅ Vous pouvez voir les erreurs
- ✅ Vous pouvez vous connecter manuellement si besoin
- ❌ Plus lent et consomme plus de ressources

### Mode headless (pour production)

```python
# config.py
HEADLESS_MODE = True
```

- ✅ Plus rapide
- ✅ Consomme moins de ressources
- ❌ Vous ne voyez pas ce qui se passe
- ⚠️ Ne fonctionne que si les cookies sont valides

## 📊 Vérifier si le bot est connecté

Regardez les logs :

```bash
tail -50 logs/bot_20251105.log | grep -i "connexion\|login\|cookies"
```

Messages de succès :
- ✅ `Connexion via cookies réussie`
- ✅ `Connexion manuelle réussie et cookies sauvegardés`
- ✅ `Selenium prêt pour les uploads`

Messages d'erreur :
- ❌ `Échec de la connexion à TikTok`
- ❌ `Le driver Selenium est fermé ou inactif`
- ❌ `Connection refused`

## 💡 Conseils

1. **Utilisez le mode visible** (`HEADLESS_MODE = False`) la première fois
2. **Laissez le navigateur ouvert** - ne le fermez pas manuellement
3. **Les cookies durent ~1 mois** - vous n'aurez pas à vous reconnecter souvent
4. **Si le bot plante**, relancez-le - il devrait se reconnecter automatiquement
5. **Vérifiez que vous n'avez pas d'extensions** qui bloquent l'automatisation

## 🆘 Toujours des problèmes ?

Essayez le script de test détaillé :

```bash
python test_connexion.py
```

Ce script va diagnostiquer exactement où ça bloque.

Si le test réussit mais le bot échoue quand même, vérifiez :
- Que vous avez assez de vidéos téléchargées
- Que les critères de filtrage ne sont pas trop stricts
- Les logs complets : `cat logs/bot_$(date +%Y%m%d).log`

