#!/usr/bin/env python3
"""
Évaluation Lighthouse comparative entre une page éco-conçue et une page anti-éco-conception.
Correction pour Windows : ajout de --no-sandbox et isolation du répertoire temporaire.
"""

import subprocess
import json
import sys
import os
import webbrowser
import threading
import http.server
import socketserver
import time
from datetime import datetime

# Configuration
URLS = {
    "Bonne page (eco)": "ecoconceptionpage.html",
    "Mauvaise page (non-eco)": "mauvaisepage.html"
}
OUTPUT_DIR = "lighthouse_reports"
PORT = 8000


def start_simple_http_server(port=PORT):
    """Démarre un serveur HTTP simple dans le répertoire courant."""
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(f"🌐 Serveur HTTP démarré sur http://localhost:{port}")
    return httpd


def run_lighthouse(url, name, output_dir):
    """Exécute Lighthouse sur une URL et retourne les métriques."""
    os.makedirs(output_dir, exist_ok=True)
    base_name = name.replace(' ', '_')
    output_base = os.path.join(output_dir, base_name)

    # Commande adaptée au système
    if sys.platform == "win32":
        lighthouse_cmd = "lighthouse.cmd"
    else:
        lighthouse_cmd = "lighthouse"

    # Ajout des flags Chrome pour éviter les erreurs de permission sous Windows
    chrome_flags = "--headless --disable-gpu --no-sandbox --disable-dev-shm-usage"

    cmd = f'{lighthouse_cmd} "{url}" --output=json,html --output-path="{output_base}" --chrome-flags="{chrome_flags}" --preset=desktop --quiet'

    print(f"🔍 Analyse Lighthouse pour : {name} ({url})")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        json_path = output_base + ".report.json"
        html_path = output_base + ".report.html"

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        categories = data.get("categories", {})
        audits = data.get("audits", {})

        metrics = {
            "performance": categories.get("performance", {}).get("score", 0) * 100,
            "accessibility": categories.get("accessibility", {}).get("score", 0) * 100,
            "best-practices": categories.get("best-practices", {}).get("score", 0) * 100,
            "seo": categories.get("seo", {}).get("score", 0) * 100,
            "total-byte-weight": audits.get("total-byte-weight", {}).get("numericValue", 0) / 1024,
            "first-contentful-paint": audits.get("first-contentful-paint", {}).get("numericValue", 0) / 1000,
            "largest-contentful-paint": audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000,
            "total-blocking-time": audits.get("total-blocking-time", {}).get("numericValue", 0),
            "cumulative-layout-shift": audits.get("cumulative-layout-shift", {}).get("numericValue", 0),
        }
        print(f"✅ Rapport généré : {json_path} et {html_path}")
        return metrics, json_path, html_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur Lighthouse pour {name}: {e.stderr}")
        # Afficher la sortie standard pour déboguer
        if e.stdout:
            print("Stdout:", e.stdout)
        if e.stderr:
            print("Stderr:", e.stderr)
        return None, None, None


def display_comparison(results):
    """Affiche un tableau comparatif dans le terminal."""
    print("\n" + "=" * 70)
    print("📊 COMPARAISON DES PERFORMANCES ÉCO-CONCEPTION (LIGHTHOUSE)")
    print("=" * 70)
    print(f"{'Métrique':<35} {'Bonne page (éco)':<20} {'Mauvaise page':<20} {'Différence':<15}")
    print("-" * 90)

    good = results["Bonne page (eco)"][0]
    bad = results["Mauvaise page (non-eco)"][0]

    for key in ["performance", "accessibility", "best-practices", "seo",
                "total-byte-weight", "first-contentful-paint", "largest-contentful-paint",
                "total-blocking-time", "cumulative-layout-shift"]:
        if key in good and key in bad:
            val_good = good[key]
            val_bad = bad[key]
            diff = val_good - val_bad
            arrow = "⬆️" if diff > 0 else "⬇️"
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
            print(f"{label:<35} {unit:<20} {unit_bad:<20} {diff_str:>7} {arrow}")

    print("\n💡 Interprétation :")
    print("  - Une bonne pratique éco-conception améliore tous les scores.")
    print("  - La page 'mauvaise' génère plus de données transférées, un JS bloquant et un CLS élevé.\n")


def generate_eco_summary(results):
    """Génère un fichier résumé textuel."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
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
        f.write("- Désactiver les trackers superflus\n")
        f.write("- Ajouter des dimensions width/height aux images\n")
        f.write("- Supprimer les intervalles intempestifs et listeners scroll sans throttling\n")
    print(f"📄 Résumé sauvegardé : {OUTPUT_DIR}/eco_audit_summary.txt")


def main():
    # Vérifier que Lighthouse est installé
    if sys.platform == "win32":
        check_cmd = "lighthouse.cmd --version"
    else:
        check_cmd = "lighthouse --version"
    try:
        subprocess.run(check_cmd, shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ Lighthouse n'est pas installé. Exécutez : npm install -g lighthouse")
        sys.exit(1)

    # Démarrer le serveur HTTP si les fichiers existent localement
    httpd = None
    server_urls = {}
    for name, path in URLS.items():
        if os.path.exists(path):
            if not httpd:
                httpd = start_simple_http_server(PORT)
            server_urls[name] = f"http://localhost:{PORT}/{path}"
        else:
            print(f"⚠️ Fichier {path} introuvable pour {name}")
            server_urls[name] = None

    results = {}
    for name, url in server_urls.items():
        if url is None:
            results[name] = (None, None, None)
            continue
        print(f"\n🚀 Lancement de Lighthouse sur {name} : {url}")
        metrics, json_path, html_path = run_lighthouse(url, name, OUTPUT_DIR)
        results[name] = (metrics, json_path, html_path)
        # Petite pause pour éviter les conflits sur le dossier Temp
        time.sleep(2)

    # Arrêter le serveur HTTP
    if httpd:
        httpd.shutdown()

    # Comparaison et affichage
    if (results.get("Bonne page (eco)")[0] is not None and
        results.get("Mauvaise page (non-eco)")[0] is not None):
        display_comparison(results)
        generate_eco_summary(results)
        webbrowser.open(results["Bonne page (eco)"][2])
        webbrowser.open(results["Mauvaise page (non-eco)"][2])
    else:
        print("⚠️ Impossible de comparer – une ou les deux analyses ont échoué.")


if __name__ == "__main__":
    main()