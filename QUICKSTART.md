# 🤖 Whiteout Survival - Autonomous Bot

## 🚀 Lancement Rapide

### 1. Prérequis

```bash
# Installer Python 3.11+
# Installer les dépendances
pip install -r requirements.txt

# Installer Ollama (IA)
# Télécharger depuis: https://ollama.ai
ollama pull moondream:1.8b
```

### 2. LDPlayer

1. Ouvre LDPlayer
2. Lance Whiteout Survival
3. Active le débogage ADB dans les paramètres

### 3. Lancer le Bot

```bash
# Mode Autonome (apprend tout seul)
python autonomous_bot.py

# OU mode Classique (avec templates)
python main.py
```

**C'est tout !** Le bot fait le reste automatiquement.

---

## 🧠 Comment il apprend

### Phase 1: Exploration (premiers lancements)

```
🔍 Le bot explore l'interface
📍 Il clique à différents endroits
📝 Il note ce qui se passe
💾 Il sauvegarde dans knowledge/
```

### Phase 2: Apprentissage

```
✅ Il mémorise les boutons qui fonctionnent
❌ Il oublie les actions qui échouent
📊 Il calcule des taux de succès
🎯 Il devient plus précis
```

### Phase 3: Optimisation

```
⚡ Il utilise ses connaissances pour farm efficacement
🔄 Il s'adapte aux changements d'UI
📈 Il s'améliore continuellement
```

---

## 📁 Structure

```
new-bot/
├── autonomous_bot.py    # 🤖 Bot autonome (apprend tout seul)
├── main.py              # 🎯 Bot classique (avec templates)
├── test_setup.py        # ✅ Tester l'installation
├── knowledge/           # 🧠 Cerveau du bot (auto-généré)
│   ├── elements.json    # Éléments UI appris
│   └── screens.json     # Écrans reconnus
├── logs/                # 📋 Logs du bot
└── templates/           # 🖼️ Templates (optionnel)
```

---

## 🎮 Modes de Fonctionnement

### Mode Autonome (Recommandé)

```bash
python autonomous_bot.py
```

**Avantages:**
- ✅ Aucun template requis
- ✅ S'adapte automatiquement
- ✅ Apprend de ses erreurs
- ✅ Devient plus intelligent avec le temps

**Inconvénients:**
- ⏱️ Plus lent au début (phase d'apprentissage)
- 🎲 Peut faire des erreurs initiales

### Mode Classique

```bash
python main.py
```

**Avantages:**
- ⚡ Rapide et précis
- 🎯 Actions optimisées

**Inconvénients:**
- 📁 Nécessite des templates
- 🔧 Configuration manuelle

---

## 📊 Progression du Bot

### Jour 1
```
🌱 Découverte de l'interface
📍 ~10-20 éléments appris
🎯 Taux de succès: ~50%
```

### Jour 7
```
📚 ~50-100 éléments appris
✅ Reconnaît tous les écrans principaux
🎯 Taux de succès: ~85%
```

### Jour 30
```
🧠 ~200+ éléments appris
⚡ Farm optimisé
🎯 Taux de succès: ~95%
```

---

## 🛠️ Commandes Utiles

```bash
# Tester l'installation
python test_setup.py

# Voir les connaissances apprises
python -c "from autonomous_bot import KnowledgeBase; kb = KnowledgeBase(); print(kb.get_stats())"

# Reset les connaissances (si besoin)
rm -rf knowledge/
```

---

## ⚠️ Important

- **Laisse tourner le bot** pour qu'il apprenne
- **Ne l'interromps pas** pendant la phase d'exploration
- **Consulte les logs** pour voir ce qu'il apprend
- **Patience** : il devient meilleur avec le temps !

---

## 📞 Support

Si problème :
1. Check les logs dans `logs/`
2. Vérifie que LDPlayer est bien en 720x1280
3. Assure-toi qu'Ollama tourne : `ollama serve`

---

**Créé avec ❤️ pour apprendre l'automatisation intelligente**
