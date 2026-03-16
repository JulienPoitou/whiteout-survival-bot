with open('C:/Users/julie/new-bot/logs/bot.log', 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')
    lines = content.split('\n')

# Compter
iterations = sum(1 for l in lines if 'Iteration' in l and '📍' in l)
clicks_ok = sum(1 for l in lines if 'Click OK' in l)
found = sum(1 for l in lines if '✓ Found' in l)
screenshots = sum(1 for l in lines if 'Screenshot:' in l)

# Templates
templates = {}
click_positions = {}
for line in lines:
    if '•' in line and 'at (' in line:
        parts = line.split('•')
        if len(parts) > 1:
            template = parts[1].split(' at')[0].strip()
            if template not in templates:
                templates[template] = 0
                click_positions[template] = []
            templates[template] += 1
            # Extraire position
            try:
                pos = line.split('at (')[1].split(')')[0]
                click_positions[template].append(pos)
            except:
                pass

# Résumé
print('=' * 70)
print('           📊 RAPPORT DÉTAILLÉ - BOT WHITEOUT SURVIVAL')
print('=' * 70)
print()
print('⏱ TEMPS DE JEU')
print('-' * 70)
print(f'  Durée totale : ~{iterations * 6 // 60} minutes')
print(f'  Itérations   : {iterations}')
print(f'  Temps moyen  : ~6 secondes par itération')
print()
print('📸 SCREENSHOTS')
print('-' * 70)
print(f'  Total           : {screenshots} screenshots')
print(f'  Résolution      : 400x652 (override 720x1280)')
print(f'  Temps par shot  : ~0.4 secondes')
print()
print('🔍 RECONNAISSANCE D\'IMAGES')
print('-' * 70)
print(f'  Templates trouvés : {found} fois')
print(f'  Seuil de confiance: 65% minimum')
print()
print('  Templates détectés :')
for t, count in sorted(templates.items(), key=lambda x: -x[1]):
    positions = click_positions.get(t, [])
    last_pos = positions[-1] if positions else 'N/A'
    print(f'    • {t:20} : {count:3} fois (dernière pos: {last_pos})')
print()
print('👆 CLICKS')
print('-' * 70)
print(f'  Clicks réussis : {clicks_ok}')
print(f'  Taux de succès : {clicks_ok/max(1,found)*100:.0f}%')
print()
print('=' * 70)
print('           🎮 CE QUE LE BOT A FAIT DANS TON JEU')
print('=' * 70)
print()
print('  Le bot a analysé l\'écran de ton jeu Whiteout Survival')
print('  et a reconnu les éléments suivants :')
print()
print('  1. 🏠 furnace_icon (icône de la fournaise)')
print('     → C\'est l\'écran d\'accueil principal du jeu')
print('     → Le bot a cliqué dessus pour naviguer/collecter')
print()
print('  2. 🔙 home_button / back_arrow')
print('     → Boutons de navigation et retour')
print('     → Le bot les a détectés mais n\'a pas cliqué')
print('       (car furnace_icon avait une meilleure confiance)')
print()
print('  COMPORTEMENT DU BOT :')
print('  ---------------------')
print('  1. 📸 Prend un screenshot de ton écran de jeu')
print('  2. 🔍 Compare avec 25 templates connus (OpenCV)')
print('  3. ✅ Vérifie la confiance (doit être > 65%)')
print('  4. 👆 Clique sur le template avec la meilleure confiance')
print('  5. ⏱ Attend 2-4 secondes (aléatoire, anti-ban)')
print('  6. 🔄 Recommence')
print()
print('  RÉSULTAT :')
print('  ----------')
print('  Le bot a cliqué ~', clicks_ok, 'fois sur l\'icône de la fournaise')
print('  pendant ~', iterations * 6 // 60, 'minutes, naviguant ainsi dans ton jeu.')
print()
print('=' * 70)
