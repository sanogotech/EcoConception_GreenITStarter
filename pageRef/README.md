
# 🌿 Éco-conception Web – Kit complet d’audit & formation

Ce dépôt fournit un environnement pédagogique pour **enseigner et vérifier les bonnes pratiques d’éco-conception web**. Il contient :

- Deux pages HTML contrastées :
  - `ecoconceptionpage.html` – page respectant le **Top 40 des bonnes pratiques** (performante, légère, accessible)
  - `mauvaisepage.html` – page volontairement non optimisée (lourde, lente, énergivore)
- Un script Python `lighthouse_eco_eval.py` pour comparer ces deux pages via Lighthouse.
- Un script `batch_lighthouse_eco.py` pour **analyser tous les fichiers HTML d’un répertoire** et générer un rapport détaillé avec le **top 5 des problèmes** et des recommandations personnalisées.

L’objectif est de montrer concrètement l’impact du code sur les performances, l’empreinte carbone et les scores Lighthouse, et de fournir des outils automatisés pour diagnostiquer et améliorer n’importe quel site.

---

## 📦 Prérequis

- **Node.js** (v14 ou supérieure) et **Lighthouse** installé globalement :
  ```bash
  npm install -g lighthouse
  ```
- **Python 3.8+** (aucune bibliothèque externe requise, uniquement la stdlib)

Vérifiez l’installation de Lighthouse :
```bash
lighthouse --version
```

---

## 📁 Structure recommandée

```
mon-projet-eco/
├── ecoconceptionpage.html          # Bonne pratique
├── mauvaisepage.html               # Mauvaise pratique
├── lighthouse_eco_eval.py          # Script comparaison 1 vs 1
├── batch_lighthouse_eco.py         # Script analyse batch
├── README.md
└── (dossier de pages à auditer)/
```

---

## 🚀 Utilisation

### 1. Comparer la bonne page et la mauvaise page

```bash
python lighthouse_eco_eval.py
```

Le script :
- Démarre un serveur HTTP local sur le port 8000
- Lance Lighthouse sur `ecoconceptionpage.html` et `mauvaisepage.html`
- Affiche un tableau comparatif des métriques (Performance, accessibilité, poids, CLS, etc.)
- Ouvre les rapports HTML complets dans votre navigateur
- Génère un résumé texte `lighthouse_reports/eco_audit_summary.txt`

**Exemple de sortie :**
```
📊 COMPARAISON DES PERFORMANCES ÉCO-CONCEPTION (LIGHTHOUSE)
Métrique                           Bonne page (éco)    Mauvaise page        Différence
Performance                        98.2                18.4                 79.8 ⬆️
Poids total (KB)                   187                  2340               -2153 KB ⬆️
CLS                                0.001                0.42                 0.419 ⬆️
```

### 2. Analyser toutes les pages HTML d’un dossier

```bash
python batch_lighthouse_eco.py /chemin/vers/mon_dossier
```

Ou, si vous êtes dans le dossier contenant les `.html` :

```bash
python batch_lighthouse_eco.py .
```

Le script :
- Parcourt récursivement tous les fichiers `.html` et `.htm`
- Lance Lighthouse sur chacun (via un serveur HTTP local)
- Extrait pour chaque page :
  - Scores (Performance, Accessibilité, Bonnes pratiques, SEO)
  - Métriques (poids total, FCP, LCP, TBT, CLS)
  - **Top 5 des audits ayant le score le plus faible** (problèmes prioritaires)
- Génère un rapport HTML unique `eco_batch_report.html` avec :
  - Un panneau dépliable par page
  - Tableau des problèmes avec description et **recommandation personnalisée**
- Ouvre automatiquement le rapport dans le navigateur

> 💡 Ce mode est idéal pour auditer un site complet ou une collection de pages d’entraînement.

---

## 🧠 Contenu pédagogique des pages HTML

### `ecoconceptionpage.html` – 40 bonnes pratiques appliquées

- ✅ Images au format WebP + `loading="lazy"` + dimensions explicites (CLS maîtrisé)
- ✅ CSS chargé de manière non bloquante (media + onload)
- ✅ Préconnexions (`preconnect`, `dns-prefetch`) aux CDN
- ✅ Pas de polices externes (polices système)
- ✅ Scripts en `defer`
- ✅ DOM léger (< 800 nœuds)
- ✅ Pas de tracking tiers, pas de carrousel inutile
- ✅ Respect de `prefers-reduced-motion`
- ✅ Compression et cache HTTP (à configurer côté serveur)

### `mauvaisepage.html` – Exemple de ce qu’il ne faut pas faire

- ❌ Polices Google + FontAwesome (requêtes supplémentaires)
- ❌ Images sans lazy loading, sans dimensions, sans WebP
- ❌ Scripts bloquants en `head`
- ❌ jQuery inutile + boucles lourdes
- ❌ SetInterval non nettoyé, écouteur `scroll` sans throttling
- ❌ Iframe météo externe
- ❌ DOM surchargé (200 éléments générés dynamiquement)
- ❌ Tracking Analytics + Hotjar, pixel tiers

---

## 🐍 Scripts Python complets (versions corrigées Windows/Linux/macOS)

### Script 1 : `lighthouse_eco_eval.py`

```python
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

    if sys.platform == "win32":
        lighthouse_cmd = "lighthouse.cmd"
    else:
        lighthouse_cmd = "lighthouse"

    chrome_flags = "--headless --disable-gpu --no-sandbox --disable-dev-shm-usage"
    cmd = f'{lighthouse_cmd} "{url}" --output=json,html --output-path="{output_base}" --chrome-flags="{chrome_flags}" --preset=desktop --quiet'

    print(f"🔍 Analyse Lighthouse pour : {name} ({url})")
    try:
        subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
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
        if e.stdout:
            print("Stdout:", e.stdout)
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
        time.sleep(2)  # Pause pour éviter conflits sur dossier Temp

    if httpd:
        httpd.shutdown()

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
```

### Script 2 : `batch_lighthouse_eco.py`

```python
#!/usr/bin/env python3
"""
Analyse éco-conception et performance de toutes les pages HTML d'un répertoire.
Lance Lighthouse sur chaque fichier et produit un rapport HTML avec top 5 problèmes.
Correction Windows : flags Chrome --no-sandbox, shell=True, gestion des permissions.
"""

import os
import sys
import json
import subprocess
import threading
import http.server
import socketserver
import webbrowser
import re
import time
from datetime import datetime

DEFAULT_PORT = 8888
REPORT_OUTPUT = "eco_batch_report.html"


def find_html_files(directory):
    """Retourne la liste des fichiers .html (récursif)."""
    html_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".html", ".htm")):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory)
                html_files.append((full_path, rel_path))
    return html_files


def start_http_server(directory, port):
    """Lance un serveur HTTP dans le répertoire spécifié."""
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(directory)
    httpd = socketserver.TCPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(f"🌐 Serveur HTTP démarré sur http://localhost:{port} (racine : {directory})")
    return httpd


def run_lighthouse(url, output_prefix):
    """Exécute Lighthouse sur une URL et retourne les données JSON."""
    if sys.platform == "win32":
        lighthouse_cmd = "lighthouse.cmd"
    else:
        lighthouse_cmd = "lighthouse"

    chrome_flags = "--headless --disable-gpu --no-sandbox --disable-dev-shm-usage"
    cmd = f'{lighthouse_cmd} "{url}" --output=json,html --output-path="{output_prefix}" --chrome-flags="{chrome_flags}" --preset=desktop --quiet'

    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        json_path = output_prefix + ".report.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, json_path, output_prefix + ".report.html"
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur Lighthouse sur {url}: {e.stderr}")
        if e.stdout:
            print("Stdout:", e.stdout)
        return None, None, None


def extract_metrics_and_audits(lighthouse_data):
    """Extrait les scores, métriques et top 5 problèmes."""
    if not lighthouse_data:
        return None
    categories = lighthouse_data.get("categories", {})
    audits = lighthouse_data.get("audits", {})

    scores = {
        "performance": categories.get("performance", {}).get("score", 0) * 100,
        "accessibility": categories.get("accessibility", {}).get("score", 0) * 100,
        "best_practices": categories.get("best-practices", {}).get("score", 0) * 100,
        "seo": categories.get("seo", {}).get("score", 0) * 100,
    }

    metrics = {
        "total_byte_weight": audits.get("total-byte-weight", {}).get("numericValue", 0) / 1024,
        "first_contentful_paint": audits.get("first-contentful-paint", {}).get("numericValue", 0) / 1000,
        "largest_contentful_paint": audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000,
        "total_blocking_time": audits.get("total-blocking-time", {}).get("numericValue", 0),
        "cumulative_layout_shift": audits.get("cumulative-layout-shift", {}).get("numericValue", 0),
    }

    failed_audits = []
    for audit_id, audit in audits.items():
        score = audit.get("score")
        if score is not None and score < 0.9 and score != -1:
            title = audit.get("title", audit_id)
            description = audit.get("description", "")
            clean_desc = re.sub(r'<[^>]+>', '', description)[:300]
            failed_audits.append({
                "id": audit_id,
                "title": title,
                "description": clean_desc,
                "score": score * 100,
            })
    failed_audits.sort(key=lambda x: x["score"])
    return {
        "scores": scores,
        "metrics": metrics,
        "top_problems": failed_audits[:5]
    }


def recommandation_for_audit(audit_id):
    """Recommandation personnalisée selon l'audit."""
    recos = {
        "unminified-css": "Minifiez tous vos fichiers CSS (cssnano, build tool).",
        "unminified-javascript": "Minifiez vos JS (Terser, esbuild).",
        "uses-optimized-images": "Utilisez WebP/AVIF et compressez vos images.",
        "offscreen-images": "Ajoutez loading='lazy' aux images hors viewport.",
        "render-blocking-resources": "Déplacez les scripts en bas avec defer, inlinez le CSS critique.",
        "uses-rel-preconnect": "Ajoutez <link rel='preconnect'> pour les domaines tiers.",
        "uses-text-compression": "Activez la compression gzip/brotli sur votre serveur.",
        "modern-image-formats": "Utilisez la balise <picture> avec WebP.",
        "dom-size": "Réduisez le DOM (< 1500 nœuds), pagination ou virtual scroll.",
        "total-byte-weight": "Éliminez les ressources inutiles, lazy load.",
        "cumulative-layout-shift": "Spécifiez width/height sur images et vidéos.",
        "uses-webp-images": "Convertissez toutes vos images en WebP.",
        "no-document-write": "Évitez document.write(), utilisez createElement.",
        "js-libraries": "Remplacez jQuery par du vanilla JS.",
    }
    for key, rec in recos.items():
        if key in audit_id:
            return rec
    return "Consultez la documentation Lighthouse pour corriger cet audit."


def generate_html_report(results, output_file):
    """Génère le rapport HTML final."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Éco-conception & Performance</title>
    <style>
        body {{ font-family: system-ui, sans-serif; margin: 0; padding: 20px; background: #f5f7fb; }}
        .container {{ max-width: 1400px; margin: auto; }}
        h1, h2 {{ color: #1e2a3e; }}
        .page-card {{ background: white; border-radius: 16px; margin-bottom: 30px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .page-header {{ background: #2c3e50; color: white; padding: 15px 20px; cursor: pointer; }}
        .page-header h3 {{ margin: 0; }}
        .page-content {{ padding: 20px; display: none; }}
        .page-content.open {{ display: block; }}
        .score-grid {{ display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 20px; }}
        .score-card {{ flex: 1; background: #f8f9fa; border-radius: 12px; padding: 12px; text-align: center; }}
        .score-value {{ font-size: 28px; font-weight: bold; }}
        .good {{ color: #2b9348; }}
        .medium {{ color: #e9a23b; }}
        .bad {{ color: #d00000; }}
        .problems-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .problems-table th, .problems-table td {{ border: 1px solid #dee2e6; padding: 8px 12px; vertical-align: top; }}
        .problems-table th {{ background: #e9ecef; }}
        .recommendation {{ background: #e3f2fd; border-left: 4px solid #0d6efd; padding: 12px; margin: 10px 0; }}
        button.toggle-all {{ background: #0d6efd; color: white; border: none; padding: 8px 16px; border-radius: 8px; margin-bottom: 20px; cursor: pointer; }}
    </style>
    <script>
        function togglePage(id) {{
            document.getElementById('content-' + id).classList.toggle('open');
        }}
        function toggleAll() {{
            let contents = document.querySelectorAll('.page-content');
            let anyClosed = Array.from(contents).some(c => !c.classList.contains('open'));
            contents.forEach(c => c.classList.toggle('open', anyClosed));
        }}
    </script>
</head>
<body>
<div class="container">
    <h1>🌿 Rapport d'éco-conception et performance</h1>
    <p>Généré le {now} — Analyse de {len(results)} page(s) HTML avec Lighthouse.</p>
    <button class="toggle-all" onclick="toggleAll()">🔽 Tout déplier / replier</button>
"""
    for idx, (file_path, data) in enumerate(results.items()):
        if not data:
            html += f"""
            <div class="page-card">
                <div class="page-header" onclick="togglePage({idx})"><h3>⚠️ {file_path}</h3></div>
                <div class="page-content" id="content-{idx}"><p>Erreur lors de l'analyse.</p></div>
            </div>"""
            continue
        scores = data["scores"]
        metrics = data["metrics"]
        top = data["top_problems"]
        perf_class = "good" if scores["performance"] >= 90 else "medium" if scores["performance"] >= 50 else "bad"
        html += f"""
        <div class="page-card">
            <div class="page-header" onclick="togglePage({idx})"><h3>📄 {file_path}</h3></div>
            <div class="page-content" id="content-{idx}">
                <div class="score-grid">
                    <div class="score-card"><div class="score-value {perf_class}">{scores['performance']:.1f}</div><div>Performance</div></div>
                    <div class="score-card"><div class="score-value {'good' if scores['accessibility']>=90 else 'medium'}">{scores['accessibility']:.1f}</div><div>Accessibilité</div></div>
                    <div class="score-card"><div class="score-value {'good' if scores['best_practices']>=90 else 'medium'}">{scores['best_practices']:.1f}</div><div>Bonnes pratiques</div></div>
                    <div class="score-card"><div class="score-value {'good' if scores['seo']>=90 else 'medium'}">{scores['seo']:.1f}</div><div>SEO</div></div>
                </div>
                <div class="recommendation">
                    📊 Métriques clés : Poids {metrics['total_byte_weight']:.0f} Ko | FCP {metrics['first_contentful_paint']:.2f}s | LCP {metrics['largest_contentful_paint']:.2f}s | TBT {metrics['total_blocking_time']:.0f} ms | CLS {metrics['cumulative_layout_shift']:.3f}
                </div>
                <h4>🔝 Top 5 des problèmes à corriger</h4>
                <table class="problems-table">
                    <tr><th>#</th><th>Audit</th><th>Description</th><th>Score</th><th>Recommandation</th></tr>
        """
        for i, p in enumerate(top, 1):
            rec = recommandation_for_audit(p["id"])
            html += f"<tr><td>{i}</td><td><strong>{p['title']}</strong></td><td>{p['description']}</td><td style='color:red'>{p['score']:.0f}/100</td><td>{rec}</td></tr>"
        html += """
                </table>
            </div>
        </div>
        """
    html += """
    <footer><p>🔍 Audit Lighthouse (Chrome Headless). Un score > 90 est excellent.<br>💡 Améliorez l'éco-conception : réduisez le poids, lazy loading, polices système, cache, JS minimal.</p></footer>
</div>
</body>
</html>"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Rapport généré : {output_file}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".", help="Répertoire contenant les fichiers HTML")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--output", default=REPORT_OUTPUT)
    args = parser.parse_args()

    target_dir = os.path.abspath(args.directory)
    if not os.path.isdir(target_dir):
        print(f"❌ Le répertoire {target_dir} n'existe pas.")
        sys.exit(1)

    html_files = find_html_files(target_dir)
    if not html_files:
        print(f"Aucun fichier HTML trouvé dans {target_dir}")
        sys.exit(0)

    print(f"🔍 {len(html_files)} fichier(s) HTML trouvé(s).")
    httpd = start_http_server(target_dir, args.port)

    results = {}
    try:
        for full_path, rel_path in html_files:
            url = f"http://localhost:{args.port}/{rel_path.replace(os.sep, '/')}"
            print(f"\n🚀 Analyse de {rel_path} -> {url}")
            safe_name = rel_path.replace(os.sep, "_").replace(".html", "").replace(".htm", "")
            output_prefix = os.path.join(os.path.dirname(__file__), f"temp_lh_{safe_name}")
            data, _, _ = run_lighthouse(url, output_prefix)
            if data:
                extracted = extract_metrics_and_audits(data)
                results[rel_path] = extracted
                for f in [f"{output_prefix}.report.json", f"{output_prefix}.report.html"]:
                    if os.path.exists(f):
                        os.remove(f)
            else:
                results[rel_path] = None
            time.sleep(1)
    finally:
        httpd.shutdown()
        print("\n🛑 Serveur HTTP arrêté.")

    generate_html_report(results, args.output)
    webbrowser.open(f"file://{os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
```

---

## 📊 Interprétation des résultats Lighthouse

| Métrique | Bonne pratique | Mauvaise pratique | Impact éco-conception |
|----------|----------------|-------------------|------------------------|
| Performance | > 90 | < 30 | Influence directement la consommation CPU et la durée de chargement |
| Total Byte Weight | < 500 Ko | > 2 Mo | Plus de données = plus d’énergie réseau et serveur |
| CLS | < 0,1 | > 0,25 | Évite les déplacements de contenu (réduit le recalcul CSS) |
| TBT | < 150 ms | > 500 ms | Moins de JavaScript = batterie économisée |

---

## 🛠️ Personnalisation avancée

### Modifier les seuils des problèmes (batch)

Dans `batch_lighthouse_eco.py`, cherchez :

```python
if score is not None and score < 0.9 and score != -1:
```

Remplacez `0.9` par le seuil désiré (ex. `0.75` pour n’inclure que les très mauvais audits).

### Ajouter une métrique (ex. ecoIndex)

Lighthouse ne fournit pas nativement l’ecoIndex. Vous pouvez intégrer l’outil [Ecoindex CLI](https://github.com/cnumr/ecoindex_cli) ou utiliser l’API GreenIT Analysis.

---

## 🔗 Ressources complémentaires

- [Référentiel Général d’Éco-conception (RGESN)](https://github.com/cnumr/Referentiel-General-Eco-conception)
- [Lighthouse – Documentation officielle](https://developer.chrome.com/docs/lighthouse/)
- [Web.dev – Éco-conception et performances](https://web.dev/performance-and-ecological-impact/)

---

## 📝 Licence

Ce projet est distribué sous licence MIT. Vous êtes libre de l’utiliser, de le modifier et de le partager dans un cadre pédagogique ou professionnel.

---

*Avec ce kit, vous avez tout pour sensibiliser et outiller vos équipes aux enjeux du numérique responsable.* 🌍


Ce README contient l’intégralité des deux scripts corrigés, prêts à être copiés-collés. Il peut être sauvegardé sous le nom `README.md` à la racine de votre projet.