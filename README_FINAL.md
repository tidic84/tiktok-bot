# 🎥 Bot TikTok - Guide Complet

## 📌 État Actuel

✅ **Le bot est fonctionnel** avec les limitations suivantes :
- **1 requête toutes les 2 heures** (rate limiting de TikTok)
- **15 vidéos max par requête** (au lieu de 50)
- **Critères assouplis** pour avoir plus de résultats

⚠️ **Limitations TikTok** :
- TikTok détecte et bloque les bots très agressivement
- Une seule requête par session fonctionne
- Les requêtes multiples déclenchent l'erreur 10201
- Le blocage est par adresse IP

---

## 🚀 Démarrage Rapide

### 1. Installation (si pas déjà fait)

```bash
cd /home/tidic/Documents/Dev/Tiktok
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuration

Éditez `config.py` si nécessaire :

```python
# Critères de sélection (déjà optimisés)
MIN_LIKES = 5000
MIN_VIEWS = 50000
MIN_ENGAGEMENT_RATE = 0.03  # 3%

# Timing (déjà optimisé)
CHECK_INTERVAL = 7200  # 2 heures
TRENDING_VIDEOS_COUNT = 15  # Nombre de vidéos par cycle
```

### 3. Lancement

```bash
python main.py
```

**OU** testez d'abord avec le debug :

```bash
python debug_scraper.py
```

---

## 📊 Ce qui Fonctionne

### ✅ Scripts qui FONCTIONNENT

1. **`debug_scraper.py`** - Test du scraper seul
   ```bash
   python debug_scraper.py
   ```
   - Récupère 10-35 vidéos
   - Teste le filtrage
   - Valide la configuration

2. **`main.py`** (version optimisée)
   - Initialise → Récupère vidéos → Ferme session
   - Attend 2 heures entre chaque cycle
   - Évite la détection de bot

---

## ⚠️ Problème TikTok Rate Limiting

### Symptôme
```
ERROR - Got an unexpected status code: statusCode: 10201
```

### Cause
TikTok bloque après :
- Trop de requêtes rapprochées
- Réutilisation de la même session
- Détection de comportement automatisé

### Solutions

#### Solution 1 : Attendre (ACTUELLE)
```python
# Dans config.py
CHECK_INTERVAL = 7200  # 2 heures minimum
TRENDING_VIDEOS_COUNT = 15  # Maximum 15-20 vidéos
```

**Attendez 30-60 minutes** si votre IP est bloquée.

#### Solution 2 : VPN/Proxy
```bash
# Utilisez un VPN et changez de serveur régulièrement
# Ou configurez un proxy dans scraper/tiktok_scraper.py
```

#### Solution 3 : API Officielle
- TikTok Research API (gratuit, académique)
- TikTok for Developers (payant, commercial)

---

## 📁 Structure du Projet

```
Tiktok/
├── main.py                    # Bot principal (OPTIMISÉ)
├── config.py                  # Configuration (OPTIMISÉE)
├── debug_scraper.py           # Test du scraper
├── cleanup.sh                 # Nettoyage des processus
│
├── scraper/
│   ├── tiktok_scraper.py     # Scraping avec TikTokApi
│   └── video_filter.py        # Filtrage des vidéos
│
├── downloader/
│   └── video_downloader.py    # Téléchargement des vidéos
│
├── uploader/
│   └── selenium_uploader.py   # Upload via Selenium
│
├── database/
│   └── db_manager.py          # Gestion SQLite
│
├── utils/
│   └── rate_limiter.py        # Gestion des délais
│
└── docs/
    ├── SOLUTION_FINALE.md     # Diagnostic complet
    ├── PROBLEME_SESSIONS_RESOLU.md
    └── ERREUR_10201_RESOLU.md
```

---

## 🔧 Dépannage

### Problème : Erreur 10201 immédiate

**Solution** :
1. Attendez 30-60 minutes (laissez l'IP se refroidir)
2. Vérifiez que vous n'avez pas de processus Playwright en cours :
   ```bash
   ./cleanup.sh
   ```
3. Testez avec `debug_scraper.py` d'abord

### Problème : Aucune vidéo ne passe les critères

**Solution** : Réduisez les critères dans `config.py` :
```python
MIN_LIKES = 1000
MIN_VIEWS = 10000
MIN_ENGAGEMENT_RATE = 0.01
```

### Problème : Playwright non installé

**Solution** :
```bash
playwright install chromium
```

### Problème : Processus bloqués

**Solution** :
```bash
./cleanup.sh
pkill -9 -f playwright
pkill -9 -f chromium
```

---

## 📝 Workflow Recommandé

### Pour Tester (Immédiat)

1. **Nettoyage** :
   ```bash
   ./cleanup.sh
   ```

2. **Attendre** : 30-60 minutes si vous venez de faire plusieurs tests

3. **Test simple** :
   ```bash
   python debug_scraper.py
   ```

4. **Si ça fonctionne**, lancez le bot :
   ```bash
   python main.py
   ```

### Pour Production (Long terme)

1. **Réduire la fréquence** :
   ```python
   CHECK_INTERVAL = 14400  # 4 heures
   ```

2. **Utiliser un proxy rotatif** ou **VPN**

3. **Surveiller les logs** :
   ```bash
   tail -f logs/bot_YYYYMMDD.log
   ```

---

## 🎯 Résultats Attendus

### Avec Configuration Actuelle

- **15 vidéos** récupérées toutes les **2 heures**
- **3-8 vidéos de qualité** après filtrage (estimation)
- **~36-96 vidéos/jour** (si aucun blocage)

### Optimisations Possibles

1. **Augmenter** `MAX_VIDEOS_PER_DAY` si vous uploadez manuellement
2. **Réduire** `CHECK_INTERVAL` si vous avez un proxy
3. **Ajuster** les critères selon vos besoins

---

## 📚 Documentation Détaillée

- **`SOLUTION_FINALE.md`** - Diagnostic complet du problème TikTok
- **`PROBLEME_SESSIONS_RESOLU.md`** - Fix du conflit Playwright/Selenium
- **`ERREUR_10201_RESOLU.md`** - Fix de l'erreur 10201 (régions)
- **`BLOCAGE_IP_TIKTOK.md`** - Comprendre le blocage IP

---

## ⚖️ Considérations Légales

⚠️ **IMPORTANT** :

- Ce bot peut violer les conditions d'utilisation de TikTok
- Le scraping n'est pas autorisé officiellement
- Les vidéos appartiennent à leurs créateurs
- Risque de blocage IP ou compte

**Alternatives légales** :
- TikTok Research API (académique)
- TikTok for Developers (commercial)
- Partenariats officiels

**Utilisez ce bot à vos propres risques.**

---

## 🆘 Support

### Logs

Les logs sont dans `logs/bot_YYYYMMDD.log`

```bash
tail -f logs/bot_$(date +%Y%m%d).log
```

### Diagnostic

1. **Test du scraper seul** :
   ```bash
   python debug_scraper.py
   ```

2. **Vérifier les processus** :
   ```bash
   ps aux | grep -E "(playwright|chromium)"
   ```

3. **Nettoyer** :
   ```bash
   ./cleanup.sh
   ```

---

## 🔄 Mises à Jour

### Prochaines Améliorations Possibles

1. ✅ Optimisation du rate limiting (FAIT)
2. ⏳ Intégration proxy rotatif
3. ⏳ Support de l'API officielle
4. ⏳ Interface web de monitoring
5. ⏳ Système de retry intelligent

---

## 📞 Contact & Contribution

Ce bot est un projet éducatif. 

**Rappel** : Le scraping de TikTok peut être illégal selon votre juridiction.

---

**Bonne chance ! 🚀**


