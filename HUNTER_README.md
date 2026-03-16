# 🔍 Template Hunter - Guide d'utilisation

## 🎯 C'est quoi ?

Un bot qui **recherche automatiquement des templates** dans ton jeu Whiteout Survival et les **teste un par un** pour trouver ceux qui marchent.

---

## 🚀 Comment l'utiliser

### Option 1 : Double-clic (Recommandé)

```
1. Double-clique sur: run_hunter.bat
2. Laisse tourner
3. Ctrl+C pour arrêter
```

### Option 2 : Ligne de commande

```bash
cd C:\Users\julie\new-bot
python hunter_launcher.py
```

---

## 📊 Ce qu'il fait

### Cycle de 10 minutes :

```
┌─────────────────────────────────────────┐
│  1. Prend un screenshot                 │
│  2. Teste TOUS les templates (500+)     │
│  3. Log les résultats                   │
│  4. Attend 10 minutes                   │
│  5. Rapport automatique                 │
│  6. Redémarre                           │
└─────────────────────────────────────────┘
```

### Templates testés :

| Source | Nombre |
|--------|--------|
| **primebot (local)** | ~400 templates |
| **wos-bot (GitHub)** | 50+ templates |
| **Total** | ~450 templates |

---

## 📁 Fichiers créés

```
new-bot/logs/
├── template_hunter.log       # Logs détaillés
├── hunter_results.json       # Résultats en temps réel
└── bot_debug_30s.log         # Anciens logs
```

---

## 📊 Rapport toutes les 10 minutes

```
================================================================================
📊 RAPPORT TEMPLATE HUNTER - 10min écoulées
================================================================================
  Progress: 150/450 (33.3%)
  Trouvés:  45 templates
  Échecs:   105 templates
  Taux:     30.0%

  TEMPLATES TROUVÉS:
    ✓ furnace_icon                 @ (166, 467) - 72.3%
    ✓ world_map_button             @ (650, 100) - 68.5%
    ✓ popup_close                  @ (52, 620) - 65.9%
    ...
================================================================================
```

---

## 🏁 À la fin (après 5h ou Ctrl+C)

```
================================================================================
🏁 CHASSE AUX TEMPLATES TERMINÉE
================================================================================
  Durée: 5h 0min
  Templates testés: 450
  Templates trouvés: 135
  Succès: 30.0%
================================================================================
✓ 135 templates copiés vers new-bot/templates/
```

---

## 🎯 Templates recherchés

### Navigation :
- `furnace_icon` - Icône fournaise (accueil)
- `world_map_button` - Bouton map monde
- `home_button` - Bouton retour accueil
- `back_arrow` - Flèche retour

### Ressources :
- `resource_meat` - Nourriture
- `resource_wood` - Bois
- `resource_coal` - Charbon
- `resource_iron` - Fer

### Actions :
- `gather_button` - Bouton collecte
- `march_button` - Bouton marche
- `search_button` - Bouton recherche
- `collect_reward` - Collecter récompense

### UI :
- `popup_close` - Fermer popup
- `popup_ok` - Bouton OK
- `popup_claim` - Réclamer
- `timer_ready` - Timer prêt
- `red_dot` - Point rouge (notification)

---

## ⚙️ Configuration

### Modifier le seuil de confiance

Dans `template_hunter.py` :

```python
self.matcher = FastTemplateMatcher(threshold=0.55)  # 55% confiance min
```

### Modifier la durée max

Dans `hunter_launcher.py` :

```python
hunter.run(max_duration_hours=10.0)  # 10 heures max
```

### Modifier l'intervalle de rapport

Dans `template_hunter.py` :

```python
if not force and (now - self.last_report_time).total_seconds() < 300:  # 5 min
```

---

## 🛑 Arrêter le bot

### Option 1 : Ctrl+C
```
Dans la fenêtre noire, appuie sur Ctrl+C
```

### Option 2 : Taskkill
```bash
taskkill /F /IM python.exe
```

---

## 📊 Voir les résultats

### En temps réel :

```bash
type logs\hunter_results.json
```

### Après la session :

```bash
type logs\template_hunter.log
```

---

## 💡 Astuces

1. **Laisse tourner la nuit** - 5h c'est long mais efficace
2. **Check les rapports** - Toutes les 10 min tu vois la progression
3. **Templates copiés auto** - À la fin, tous les templates trouvés sont dans `templates/`
4. **Utilise avec fast_bot.py** - Une fois les templates trouvés, lance `fast_bot.py` pour les utiliser

---

## 🚨 Problèmes connus

| Problème | Solution |
|----------|----------|
| **ADB not found** | Vérifie que LDPlayer est ouvert |
| **Screenshot failed** | Redémarre LDPlayer |
| **0 templates trouvés** | Baisse le seuil à 0.50 dans le code |
| **Trop lent** | Réduis le nombre de sources dans TEMPLATE_SOURCES |

---

## ✅ Checklist avant de lancer

- [ ] LDPlayer est ouvert
- [ ] Whiteout Survival est lancé
- [ ] Résolution: 720x1280
- [ ] ADB debugging: activé
- [ ] Ollama: tourne (optionnel)

---

**Prêt à chasser des templates !** 🎯
