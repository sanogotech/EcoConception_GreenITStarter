#!/usr/bin/env python3
"""
Évaluation Lighthouse comparative entre une page éco-conçue (bonne-page.html)
et une page anti-éco-conception (mauvaise-page.html).
Génère un rapport JSON/HTML et affiche les scores clés.
Nécessite : Node.js, Lighthouse (npm install -g lighthouse) et Python 3.8+
"""

import subprocess
import json
import sys
import os
import webbrowser
from datetime import datetime

# Configuration
URLS = {
    "Bonne page (eco)": "bonne-page.html",      # Remplacez par le chemin absolu ou serveur local
    "Mauvaise page (non-eco)": "mauvaise-page.html"
}
OUTPUT_DIR = "lighthouse_reports"
PORT = 8000  # port pour serveur HTTP local si fichiers locaux

def start_simple_http_server(port=PORT):
    """Démarre un serveur HTTP simple dans le répertoire courant pour servir les fichiers HTML."""
    import threading
    import http.server
    import socketserver

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serveur HTTP démarré sur http://localhost:{port}")
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return httpd

def run_lighthouse(url, name, output_dir):
    """Exécute Lighthouse sur une URL et retourne les métriques clés."""
    report_path = os.path.join(output_dir, f"{name.replace(' ', '_')}_report.json")
    html_path = os.path.join(output_dir, f"{name.replace(' ', '_')}_report.html")
    
    cmd = [
        "lighthouse", url,
        "--output=json,html",
        "--output-path=" + report_path.replace(".json", ""),  # enlève l'extension, lighthouse ajoute .json/.html
        "--chrome-flags=--headless --disable-gpu",
        "--preset=desktop",  # on peut changer pour mobile
        "--quiet"
    ]
    # Correction nom de sortie : Lighthouse génère <output-path>.report.html/.json
    # On va forcer avec --output-path sans extension
    cmd[cmd.index("--output-path") + 1] = os.path.splitext(report_path)[0]
    
    print(f"🔍 Analyse Lighthouse pour : {name} ({url})")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Charger le fichier JSON généré
        actual_json = os.path.splitext(report_path)[0] + ".report.json"
        with open(actual_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        categories = data.get("categories", {})
        audits = data.get("audits", {})
        metrics = {
            "performance": categories.get("performance", {}).get("score", 0) * 100,
            "accessibility": categories.get("accessibility", {}).get("score", 0) * 100,
            "best-practices": categories.get("best-practices", {}).get("score", 0) * 100,
            "seo": categories.get("seo", {}).get("score", 0) * 100,
            "total-byte-weight": audits.get("total-byte-weight", {}).get("numericValue", 0) / 1024,  # KB
            "first-contentful-paint": audits.get("first-contentful-paint", {}).get("numericValue", 0) / 1000,
            "largest-contentful-paint": audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000,
            "total-blocking-time": audits.get("total-blocking-time", {}).get("numericValue", 0),
            "cumulative-layout-shift": audits.get("cumulative-layout-shift", {}).get("numericValue", 0),
        }
        # Sauvegarde également du HTML
        print(f"✅ Rapport généré : {actual_json} et {html_path}")
        return metrics, actual_json, html_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur Lighthouse pour {name}: {e.stderr}")
        return None, None, None

def display_comparison(results):
    """Affiche un tableau comparatif dans le terminal."""
    print("\n" + "="*70)
    print("📊 COMPARAISON DES PERFORMANCES ÉCO-CONCEPTION (LIGHTHOUSE)")
    print("="*70)
    headers = ["Métrique", "Bonne page (éco)", "Mauvaise page", "Différence"]
    print(f"{headers[0]:<35} {headers[1]:<20} {headers[2]:<20} {headers[3]:<15}")
    print("-"*90)
    
    for key in ["performance", "accessibility", "best-practices", "seo", "total-byte-weight", "first-contentful-paint", "largest-contentful-paint", "total-blocking-time", "cumulative-layout-shift"]:
        if key in results["Bonne page (eco)"][0] and key in results["Mauvaise page (non-eco)"][0]:
            val_good = results["Bonne page (eco)"][0][key]
            val_bad = results["Mauvaise page (non-eco)"][0][key]
            diff = val_good - val_bad
            # Formattage selon le type
            if "byte" in key or "weight" in key:
                label = "Poids total (KB)"
                unit = f"{val_good:.1f} KB"
                unit_bad = f"{val_bad:.1f} KB"
                diff_str = f"{diff:.1f} KB"
            elif "paint" in key or "fcp" in key or "lcp" in key:
                label = key.replace("-", " ").title()
                unit = f"{val_good:.2f} s"
                unit_bad = f"{val_bad:.2f} s"
                diff_str = f"{diff:.2f} s"
            elif "blocking" in key:
                label = "Temps blocage total (ms)"
                unit = f"{val_good:.0f} ms"
                unit_bad = f"{val_bad:.0f} ms"
                diff_str = f"{diff:.0f} ms"
            elif "layout-shift" in key:
                label = "CLS (Cumul. Layout Shift)"
                unit = f"{val_good:.3f}"
                unit_bad = f"{val_bad:.3f}"
                diff_str = f"{diff:.3f}"
            else:
                label = key.replace("-", " ").title()
                unit = f"{val_good:.1f}"
                unit_bad = f"{val_bad:.1f}"
                diff_str = f"{diff:.1f}"
            
            # Ajout du symbole d'amélioration
            arrow = "⬆️" if diff > 0 else "⬇️"
            print(f"{label:<35} {unit:<20} {unit_bad:<20} {diff_str:>7} {arrow}")
    
    print("\n💡 Interprétation :")
    print("  - Une bonne pratique éco-conception améliore tous les scores (Performance, ecoIndex).")
    print("  - La page 'mauvaise' génère plus de données transférées, un JS bloquant et un CLS élevé.")
    print("  - Utilisez Lighthouse CI pour automatiser ces tests en production.\n")

def generate_eco_summary(results):
    """Génère un petit résumé avec commentaires sur les améliorations."""
    with open(os.path.join(OUTPUT_DIR, "eco_audit_summary.txt"), "w", encoding="utf-8") as f:
        f.write("RAPPORT D'AUDIT ÉCO-CONCEPTION\n")
        f.write(f"Date : {datetime.now()}\n\n")
        good_score = results["Bonne page (eco)"][0]["performance"]
        bad_score = results["Mauvaise page (non-eco)"][0]["performance"]
        f.write(f"✅ Bonne page : Performance Lighthouse = {good_score:.1f}/100\n")
        f.write(f"❌ Mauvaise page : Performance Lighthouse = {bad_score:.1f}/100\n")
        f.write(f"📉 Écart de performance : {good_score - bad_score:.1f} points.\n\n")
        f.write("Recommandations pour corriger la 'mauvaise page' :\n")
        f.write("- Appliquer lazy loading sur toutes les images (<img loading='lazy'>)\n")
        f.write("- Convertir les images en WebP et ajouter srcset\n")
        f.write("- Supprimer les polices externes (utiliser système)\n")
        f.write("- Déplacer les scripts JS en bas de page avec defer/async\n")
        f.write("- Éviter les iframes et widgets météo inutiles\n")
        f.write("- Réduire le DOM (< 1000 nœuds)\n")
        f.write("- Mettre en cache statique, minifier CSS/JS\n")
        f.write("- Désactiver les trackers superflus (GA, Hotjar)\n")
        f.write("- Ajouter des dimensions width/height aux images\n")
        f.write("- Supprimer les intervalle intempestifs et listeners scroll sans throttling\n")
        f.write("- Utiliser des animations CSS réduites et respecter prefers-reduced-motion\n")
    print(f"📄 Résumé sauvegardé : {OUTPUT_DIR}/eco_audit_summary.txt")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Vérifier si lighthouse est installé
    try:
        subprocess.run(["lighthouse", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("❌ Lighthouse n'est pas installé. Exécutez : npm install -g lighthouse")
        sys.exit(1)
    
    # Servir les fichiers localement si ce sont des chemins relatifs
    httpd = None
    server_urls = {}
    for name, path in URLS.items():
        if os.path.exists(path):
            # On lance un serveur HTTP simple si besoin (évite les CORS/file protocol)
            if not httpd:
                httpd = start_simple_http_server(PORT)
            server_urls[name] = f"http://localhost:{PORT}/{path}"
        else:
            # Si c'est déjà une URL distante
            server_urls[name] = path
    
    results = {}
    for name, url in server_urls.items():
        print(f"\n🚀 Lancement de Lighthouse sur {name} : {url}")
        metrics, json_path, html_path = run_lighthouse(url, name, OUTPUT_DIR)
        if metrics:
            results[name] = (metrics, json_path, html_path)
        else:
            results[name] = (None, None, None)
    
    if httpd:
        httpd.shutdown()
    
    # Comparaison
    if "Bonne page (eco)" in results and "Mauvaise page (non-eco)" in results:
        if results["Bonne page (eco)"][0] and results["Mauvaise page (non-eco)"][0]:
            display_comparison(results)
            generate_eco_summary(results)
            # Ouverture automatique des rapports HTML dans le navigateur
            webbrowser.open(results["Bonne page (eco)"][2])
            webbrowser.open(results["Mauvaise page (non-eco)"][2])
        else:
            print("⚠️ Impossible de comparer car un des audits a échoué.")
    else:
        print("Les deux pages n'ont pas pu être testées. Vérifiez les chemins.")

if __name__ == "__main__":
    main()
