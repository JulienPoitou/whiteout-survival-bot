# Templates de Navigation pour Whiteout Survival

## Comment créer les templates

1. **Lancez Whiteout Survival** sur LDPlayer
2. **Faites une capture d'écran** complète (720x1280)
3. **Découpez les éléments** suivants avec un éditeur d'images

## Templates Requis

### Navigation Principale

| Nom du fichier | Description | Taille approx. |
|----------------|-------------|----------------|
| `furnace_icon.png` | Icône de la fournaise (écran d'accueil) | 60x60 |
| `world_map_button.png` | Bouton pour aller à la map monde | 80x40 |
| `world_map_ui.png` | UI de la map monde (coin supérieur) | 200x100 |
| `home_button.png` | Bouton retour accueil | 50x50 |
| `search_button.png` | Bouton de recherche (gather) | 100x50 |

### Ressources

| Nom du fichier | Description |
|----------------|-------------|
| `resource_meat_icon.png` | Icône de nourriture |
| `resource_wood_icon.png` | Icône de bois |
| `resource_coal_icon.png` | Icône de charbon |
| `resource_iron_icon.png` | Icône de fer |

### Actions

| Nom du fichier | Description |
|----------------|-------------|
| `gather_deploy_button.png` | Bouton pour gather |
| `march_button.png` | Bouton pour envoyer la marche |
| `popup_close.png` | Bouton fermer popup |
| `popup_x.png` | Croix de fermeture |

## Comment découper les templates

### Méthode 1: Paint.NET (Windows)
1. Ouvrez le screenshot
2. Outil de sélection rectangulaire
3. Sélectionnez l'élément
4. Ctrl+Shift+X (cropper)
5. Enregistrer sous → PNG

### Méthode 2: GIMP (Gratuit)
1. Ouvrez le screenshot
2. Outil de sélection
3. Sélectionnez l'élément
4. Image → Rogner selon la sélection
5. Exporter → PNG

### Méthode 3: Python Script
```python
from PIL import Image

# Ouvrir screenshot
img = Image.open("screenshot.png")

# Découper (ajuster les coordonnées)
# Format: (left, top, right, bottom)
template = img.crop((100, 200, 160, 260))

# Sauvegarder
template.save("furnace_icon.png")
```

## Conseils pour de bons templates

✅ **À FAIRE:**
- Templates de 50x50 à 150x150 pixels
- Éléments avec contours nets
- Inclure un peu de contexte autour
- Format PNG sans compression

❌ **À ÉVITER:**
- Templates trop petits (< 30x30)
- Éléments flous
- Texte seul (préférer OCR)
- Zones trop uniformes

## Emplacements typiques (720x1280)

```
┌─────────────────────────────────┐
│  HOME    (50,50)                │  ← home_button
│                                 │
│                                 │
│         [Fournaise]             │  ← furnace_icon (330, 500)
│                                 │
│                                 │
│    [World]                      │  ← world_map_button (600, 100)
└─────────────────────────────────┘
```

## Vérification

Après avoir créé les templates, lancez :

```bash
python test_setup.py
```

Le test vérifiera que les templates sont bien chargés.
