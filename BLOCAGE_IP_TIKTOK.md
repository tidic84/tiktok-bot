# 🚨 Blocage IP TikTok - Guide Complet

## 🔍 Diagnostic

Votre IP a été **bloquée temporairement** par TikTok à cause de multiples tentatives rapides.

### Chronologie des Tentatives
```
15:32 → Échec (erreur 10201)
15:44 → Échec (erreur 10201)
15:53 → Échec (erreur 10201)
18:49 → Échec (erreur 10201) ← Vous êtes ici
```

**Résultat:** TikTok a identifié un comportement suspect et a bloqué votre IP.

---

## 🛠️ Solutions (par ordre de facilité)

### Solution 1️⃣ : Attendre (Recommandé) 🕐

**La plus simple et la plus sûre**

```
⏰ Durée : 2-4 heures
✅ Efficacité : 95%
💰 Coût : Gratuit
```

**Étapes :**
1. **Arrêtez le bot** (Ctrl+C)
2. **Attendez 2-4 heures** sans faire de requêtes
3. **Vérifiez** avec le script de test :
   ```bash
   python debug_scraper.py
   ```
4. Si vous voyez "✓ XX vidéos", c'est bon !
5. Relancez le bot : `python main.py`

**Pourquoi ça marche :**
- TikTok utilise un rate limiting temporaire
- Le blocage expire automatiquement
- Votre historique se "nettoie"

---

### Solution 2️⃣ : Changer d'IP (Redémarrage Box) 🌐

**Rapide et efficace**

```
⏰ Durée : 5-10 minutes
✅ Efficacité : 90%
💰 Coût : Gratuit
```

**Étapes :**
1. **Débranchez** votre box internet (ou routeur)
2. **Attendez 2 minutes** (important !)
3. **Rebranchez** et attendez que tout redémarre
4. **Vérifiez votre nouvelle IP** :
   ```bash
   curl ifconfig.me
   ```
5. **Testez le bot** :
   ```bash
   python debug_scraper.py
   ```

**Note :** Certains FAI ne changent pas l'IP immédiatement. Si ça ne marche pas, attendez 15-30 minutes de plus avant de rebrancher.

---

### Solution 3️⃣ : Utiliser un VPN 🔒

**Efficace mais nécessite installation**

```
⏰ Durée : 10-15 minutes (installation comprise)
✅ Efficacité : 95%
💰 Coût : Gratuit (ProtonVPN) ou payant
```

**VPN Recommandés :**

**Gratuit :**
- **ProtonVPN** (recommandé) : https://protonvpn.com
  ```bash
  # Installation Arch Linux
  yay -S protonvpn-cli
  
  # Connexion
  protonvpn-cli connect --fastest
  ```

**Payant (plus stable) :**
- Mullvad VPN
- NordVPN
- ExpressVPN

**Étapes :**
1. **Installez** un VPN
2. **Connectez-vous** à un serveur **américain** (important !)
3. **Vérifiez votre IP** :
   ```bash
   curl ifconfig.me
   # Devrait montrer une IP américaine
   ```
4. **Testez** :
   ```bash
   python debug_scraper.py
   ```

**Pourquoi serveur US ?**
Le bot est configuré pour `locale: en-US`, donc un serveur US est plus cohérent.

---

### Solution 4️⃣ : Utiliser des Proxies (Avancé) 🔄

**Pour utilisateurs avancés**

```
⏰ Durée : 30+ minutes
✅ Efficacité : 99%
💰 Coût : Payant (proxies résidentiels recommandés)
```

**Services de Proxies :**
- Bright Data (anciennement Luminati)
- Oxylabs
- Smartproxy

**Configuration :**

1. **Obtenir des proxies** (payant, ~$5-10/GB)

2. **Modifier config.py** :
   ```python
   # Ajouter à la classe Config
   PROXY_URL = "http://user:pass@proxy-server:port"
   ```

3. **Modifier scraper/tiktok_scraper.py** :
   ```python
   await self.api.create_sessions(
       num_sessions=1,
       sleep_after=3,
       headless=self.config.HEADLESS_MODE,
       context_options={
           "locale": "en-US",
           "timezone_id": "America/New_York"
       },
       proxies=[self.config.PROXY_URL]  # Ajouter ici
   )
   ```

---

## 🧪 Script de Vérification

**Avant de relancer le bot**, vérifiez toujours que votre IP fonctionne :

```bash
cd /home/tidic/Documents/Dev/Tiktok
source venv/bin/activate
python debug_scraper.py
```

**Résultats possibles :**

✅ **SUCCÈS** :
```
✓ 10 vidéos récupérées
✓ TEST TERMINÉ AVEC SUCCÈS
```
→ Vous pouvez lancer le bot !

❌ **ÉCHEC** :
```
ERROR statusCode: 10201
✓ 0 vidéos récupérées
```
→ IP toujours bloquée, essayez une autre solution

---

## ⚠️ Prévention Future

Pour éviter les blocages à l'avenir :

### 1. Augmenter les délais

Dans `config.py` :
```python
CHECK_INTERVAL = 7200  # 2 heures au lieu de 1 heure
MIN_DELAY_BETWEEN_UPLOADS = 1800  # 30 min au lieu de 5 min
```

### 2. Limiter les vidéos par jour

```python
MAX_VIDEOS_PER_DAY = 10  # Au lieu de 20
TRENDING_VIDEOS_COUNT = 30  # Au lieu de 50
HASHTAG_VIDEOS_COUNT = 20  # Au lieu de 30
```

### 3. Éviter les relances multiples

**Ne relancez PAS le bot immédiatement** si il ne trouve pas de vidéos !
- Vérifiez d'abord avec `debug_scraper.py`
- Si échec, attendez ou changez d'IP
- Puis relancez

### 4. Utiliser un VPN de base

Même sans blocage, un VPN peut :
- Éviter les détections
- Distribuer les requêtes
- Augmenter la stabilité

---

## 📊 Tableau Comparatif des Solutions

| Solution | Temps | Difficulté | Efficacité | Coût |
|----------|-------|------------|------------|------|
| **Attendre** | 2-4h | ⭐ | ⭐⭐⭐⭐⭐ | Gratuit |
| **Redémarrer box** | 5-10min | ⭐⭐ | ⭐⭐⭐⭐ | Gratuit |
| **VPN gratuit** | 10-15min | ⭐⭐⭐ | ⭐⭐⭐⭐ | Gratuit |
| **VPN payant** | 10min | ⭐⭐ | ⭐⭐⭐⭐⭐ | ~$5/mois |
| **Proxies** | 30+min | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ~$50+/mois |

---

## 🎯 Recommandation Personnelle

**Pour votre cas (utilisateur intermédiaire) :**

1. **Maintenant** : Redémarrer la box internet (5 min)
2. **Si ça ne marche pas** : Installer ProtonVPN gratuit
3. **Pour l'avenir** : Augmenter les délais dans la config

**Commandes rapides :**
```bash
# Test après changement d'IP
python debug_scraper.py

# Si succès, lancer le bot
python main.py

# Surveiller en temps réel
tail -f logs/bot_$(date +%Y%m%d).log
```

---

## 💡 Astuces Supplémentaires

### Vérifier votre IP actuelle
```bash
curl ifconfig.me
# ou
curl api.ipify.org
```

### Voir l'historique des blocages
```bash
grep "10201" logs/*.log | wc -l
# Compte le nombre d'erreurs 10201
```

### Nettoyer les sessions Playwright
```bash
rm -rf ~/.cache/ms-playwright/
playwright install
```

---

## ❓ FAQ

**Q: Combien de temps dure un blocage IP ?**
R: Généralement 2-4 heures, parfois jusqu'à 24h pour des violations répétées.

**Q: Puis-je utiliser Tor ?**
R: Déconseillé. Tor est lent et les IPs Tor sont souvent déjà bannies.

**Q: Un VPN gratuit suffit-il ?**
R: Oui, ProtonVPN gratuit fonctionne bien pour ce cas d'usage.

**Q: Que faire si toutes les solutions échouent ?**
R: Attendez 24-48h. C'est le temps maximum des blocages temporaires.

---

**Bonne chance ! N'oubliez pas de vérifier avec `debug_scraper.py` avant de relancer le bot.** 🚀


