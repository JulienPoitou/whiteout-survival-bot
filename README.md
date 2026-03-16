# 🤖 Whiteout Survival Bot - Template Hunter v3

Bot autonome pour Whiteout Survival qui **apprend tout seul** en explorant le jeu et en testant des templates.

---

## 🚀 Démarrage Rapide

### 1. Prérequis

```bash
# Installer Python 3.11+
# Installer les dépendances
pip install -r requirements.txt

# Installer Ollama (optionnel, pour IA)
# https://ollama.ai
ollama pull moondream:1.8b
```

### 2. Configuration LDPlayer

- **Résolution** : 720 x 1280
- **DPI** : 240
- **ADB Debugging** : Activé
- **Port** : 5555

### 3. Lancer le Bot

```bash
# Mode Template Hunter (recommandé)
python hunter_v3.py

# Mode Fast Bot (avec templates existants)
python fast_bot.py

# Mode Autonome (IA + apprentissage)
python autonomous_bot.py
```

---

## 📁 Structure du Projet

```
new-bot/
├── hunter_v3.py           # 🔍 Template Hunter - Explore et apprend
├── fast_bot.py            # ⚡ Bot rapide - Utilise templates existants
├── autonomous_bot.py      # 🧫 Bot autonome - IA + apprentissage
├── config.py              # Configuration générale
├── .env                   # Variables d'environnement
│
├── adb/
│   └── controller.py      # Contrôle ADB (screenshots, taps)
├── vision/
│   ├── fast_matcher.py    # Template matching OpenCV (RAPIDE)
│   ├── ai_analyzer.py     # Analyse IA (Ollama)
│   └── ocr_reader.py      # OCR (Tesseract)
├── core/
│   ├── context.py         # Mémoire du bot (états visités)
│   └── vision_facade.py   # Routeur de vision
├── tasks/
│   ├── base.py            # Classe de base des tâches
│   └── gather.py          # Task de farm de ressources
│
├── templates/             # Templates d'images
├── knowledge/             # Mémoire (auto-généré)
└── logs/                  # Logs (auto-généré)
```

---

## 🔍 Template Hunter v3

Le bot **explore le jeu** et **trouve tout seul** les templates qui marchent.

### Fonctionnalités

- ✅ **Screen Hashing** : Détecte les écrans déjà vus (anti-boucle)
- ✅ **Auto-Back** : Retour automatique si bloqué 10s
- ✅ **Template Blacklist** : Ignore les templates après 3 clics sans succès
- ✅ **Exploration Auto** : Clique et navigue dans le jeu
- ✅ **Rapports 10min** : Résumé toutes les 10 minutes

### Logs en Temps Réel

```bash
# Dans un autre terminal
python watch_logs.bat
# OU
powershell -Command "Get-Content logs\hunter_v3.log -Wait -Tail 30"
```

---

## ⚡ Fast Bot

Utilise les templates **déjà trouvés** pour farmer efficacement.

```bash
python fast_bot.py
```

---

## 🧠 Bot Autonome

Combine **Template Matching + IA** pour un apprentissage intelligent.

```bash
python autonomous_bot.py
```

---

## 🛠️ Commandes Utiles

```bash
# Tester l'installation
python test_setup.py

# Voir les templates trouvés
type logs\hunter_results.json

# Nettoyer les screenshots
del /Q _scr_*.png

# Arrêter le bot
taskkill /F /IM python.exe
```

---

## 📊 Performance

| Métrique | Avant | Après |
|----------|-------|-------|
| Screenshot | 60-90s | **0.4s** |
| Template Matching | 15-30s (IA) | **0.001s** |
| Click Success Rate | 50% | **100%** |
| Iteration Time | ~120s | **~2s** |

**Gain total : ~60x plus rapide !** 🚀

---

## 🔧 Dépannage

### ADB ne se connecte pas

```bash
# Vérifier ADB
adb devices

# Redémarrer ADB
adb kill-server
adb start-server

# Utiliser le bon ADB (version 41)
C:\Users\julie\AppData\Local\Android\Sdk\platform-tools\adb.exe devices
```

### Templates pas trouvés

- Vérifier que LDPlayer est en **720x1280**
- Copier les templates depuis `primebot/images/whiteout/`
- Baisser le seuil dans `hunter_v3.py` : `threshold=0.55`

### Bot clique pas

- Donner le **focus** à la fenêtre LDPlayer
- Vérifier que le jeu est **ouvert et actif**
- Tester un tap direct :
  ```bash
  adb shell input tap 360 640
  ```

---

## 📝 License

Projet personnel à but éducatif. Utilisez à vos risques et périls.

---

**Créé avec ❤️ pour Whiteout Survival**
