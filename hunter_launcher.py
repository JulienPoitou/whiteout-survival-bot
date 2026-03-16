#!/usr/bin/env python
"""
Template Hunter - Auto Restarter
Lance le hunter et le relance toutes les 10 minutes avec rapport
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def print_header():
    print("\n" + "=" * 80)
    print("🔍 TEMPLATE HUNTER - AUTO RESTARTER")
    print("=" * 80)
    print(f"  Démarré à: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Rapport toutes les: 10 minutes")
    print("  Durée max par session: 10 minutes")
    print("  Redémarrage: Automatique")
    print("=" * 80 + "\n")

def run_hunter(session_num: int) -> bool:
    """Lance une session du hunter"""
    start_time = datetime.now()
    print(f"\n{'='*80}")
    print(f"🚀 SESSION {session_num} - {start_time.strftime('%H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        # Lancer le hunter
        result = subprocess.run(
            [sys.executable, "template_hunter.py"],
            cwd=Path(__file__).parent,
            timeout=700,  # 11 min 40 sec max
            capture_output=False
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n{'='*80}")
        print(f"✅ SESSION {session_num} TERMINÉE")
        print(f"  Durée: {duration}")
        print(f"  Code retour: {result.returncode}")
        print(f"{'='*80}\n")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n{'='*80}")
        print(f"⏰ SESSION {session_num} - TIMEOUT APRÈS {duration}")
        print(f"{'='*80}\n")
        return False
        
    except KeyboardInterrupt:
        print(f"\n{'='*80}")
        print(f"⚠️  SESSION {session_num} - INTERROMPU PAR L'UTILISATEUR")
        print(f"{'='*80}\n")
        return False
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ SESSION {session_num} - ERREUR: {e}")
        print(f"{'='*80}\n")
        return False

def show_report():
    """Affiche un rapport rapide des résultats"""
    results_file = LOG_DIR / "hunter_results.json"
    
    if not results_file.exists():
        return
    
    try:
        import json
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n{'='*80}")
        print("📊 RAPIDE DES RÉSULTATS")
        print(f"{'='*80}")
        print(f"  Templates testés: {data['stats']['total_tested']}")
        print(f"  Templates trouvés: {data['stats']['total_found']}")
        print(f"  Taux de succès: {data['stats']['success_rate']*100:.1f}%")
        
        if data['found']:
            print(f"\n  DERNIERS TROUVÉS:")
            found_list = list(data['found'].values())[-5:]
            for t in found_list:
                print(f"    ✓ {t['name']} @ ({t['x']}, {t['y']}) - {t['confidence']:.1%}")
        
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"Error reading results: {e}\n")

def main():
    """Boucle principale"""
    print_header()
    
    session_num = 0
    total_found = 0
    
    try:
        while True:
            session_num += 1
            
            # Lancer le hunter
            success = run_hunter(session_num)
            
            # Afficher le rapport
            show_report()
            
            # Compter les templates trouvés
            try:
                import json
                results_file = LOG_DIR / "hunter_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    total_found = data['stats']['total_found']
            except:
                pass
            
            # Pause de 30 secondes avant restart
            print(f"⏱  Prochain lancement dans 30 secondes...")
            time.sleep(30)
            
            # Auto-restart
            print(f"🔄 REDÉMARRAGE AUTOMATIQUE...\n")
            
    except KeyboardInterrupt:
        print(f"\n{'='*80}")
        print(f"🛑 ARRÊT DEMANDÉ PAR L'UTILISATEUR")
        print(f"{'='*80}")
        print(f"  Sessions totales: {session_num}")
        print(f"  Templates trouvés: {total_found}")
        print(f"  Logs: {LOG_DIR / 'template_hunter.log'}")
        print(f"  Résultats: {LOG_DIR / 'hunter_results.json'}")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
