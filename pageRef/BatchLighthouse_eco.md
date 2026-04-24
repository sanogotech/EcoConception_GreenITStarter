# 📦 Script : `batch_lighthouse_eco.py`

```python
#!/usr/bin/env python3
"""
Analyse éco-conception et performance de toutes les pages HTML d'un répertoire.
Lance Lighthouse sur chaque fichier, extrait les métriques clés et les audits critiques,
et produit un rapport HTML complet avec le top 5 des problèmes par page.
"""

import os
import sys
import json
import subprocess
import threading
import http.server
import socketserver
import webbrowser
from datetime import datetime
from pathlib import Path

# Configuration
DEFAULT_PORT = 8888
REPORT_OUTPUT = "eco_batch_report.html"

def find_html_files(directory):
    """Retourne la liste de tous les fichiers .html dans directory (récursif)."""
    html_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html") or file.endswith(".htm"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory)
                html_files.append((full_path, rel_path))
    return html_files

def start_http_server(directory, port):
    """Lance un serveur HTTP dans le répertoire spécifié."""
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(directory)  # Le serveur sert à partir de ce répertoire
    httpd = socketserver.TCPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(f"🌐 Serveur HTTP démarré sur http://localhost:{port} (racine : {directory})")
    return httpd

def run_lighthouse(url, output_prefix):
    """Exécute Lighthouse sur une URL et retourne les données JSON."""
    json_path = f"{output_prefix}.report.json"
    html_path = f"{output_prefix}.report.html"
    cmd = [
        "lighthouse", url,
        "--output=json,html",
        "--output-path=" + output_prefix,
        "--chrome-flags=--headless --disable-gpu",
        "--preset=desktop",
        "--quiet"
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, json_path, html_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur Lighthouse sur {url}: {e.stderr}")
        return None, None, None

def extract_metrics_and_audits(lighthouse_data):
    """Extrait les scores catégories + métriques + liste des audits échoués."""
    if not lighthouse_data:
        return None
    categories = lighthouse_data.get("categories", {})
    audits = lighthouse_data.get("audits", {})
    
    # Scores principaux (0-100)
    scores = {
        "performance": categories.get("performance", {}).get("score", 0) * 100,
        "accessibility": categories.get("accessibility", {}).get("score", 0) * 100,
        "best_practices": categories.get("best-practices", {}).get("score", 0) * 100,
        "seo": categories.get("seo", {}).get("score", 0) * 100,
    }
    
    # Métriques techniques
    metrics = {
        "total_byte_weight": audits.get("total-byte-weight", {}).get("numericValue", 0) / 1024,  # KB
        "first_contentful_paint": audits.get("first-contentful-paint", {}).get("numericValue", 0) / 1000,  # s
        "largest_contentful_paint": audits.get("largest-contentful-paint", {}).get("numericValue", 0) / 1000,
        "total_blocking_time": audits.get("total-blocking-time", {}).get("numericValue", 0),  # ms
        "cumulative_layout_shift": audits.get("cumulative-layout-shift", {}).get("numericValue", 0),
    }
    
    # Récupérer tous les audits avec un score < 0.9 (problèmes)
    failed_audits = []
    for audit_id, audit in audits.items():
        score = audit.get("score")
        if score is not None and score < 0.9 and score != -1:  # -1 = non applicable
            title = audit.get("title", audit_id)
            description = audit.get("description", "")
            # Nettoyer la description (supprimer les balises HTML)
            import re
            clean_desc = re.sub(r'<[^>]+>', '', description)
            failed_audits.append({
                "id": audit_id,
                "title": title,
                "description": clean_desc[:300],
                "score": score * 100,
                "weight": audit.get("weight", 0)
            })
    # Trier par score croissant (les pires en premier)
    failed_audits.sort(key=lambda x: x["score"])
    return {
        "scores": scores,
        "metrics": metrics,
        "top_problems": failed_audits[:5]  # Top 5 des pires problèmes
    }

def generate_html_report(results, output_file):
    """Génère un rapport HTML complet avec tableau récapitulatif et détails."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Éco-conception & Performance - Batch Lighthouse</title>
    <style>
        body {{ font-family: system-ui, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f7fb; }}
        .container {{ max-width: 1400px; margin: auto; }}
        h1, h2 {{ color: #1e2a3e; }}
        .summary {{ background: white; border-radius: 16px; padding: 20px; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .page-card {{ background: white; border-radius: 16px; margin-bottom: 30px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .page-header {{ background: #2c3e50; color: white; padding: 15px 20px; cursor: pointer; }}
        .page-header h3 {{ margin: 0; }}
        .page-content {{ padding: 20px; display: none; }}
        .page-content.open {{ display: block; }}
        .score-grid {{ display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 20px; }}
        .score-card {{ flex: 1; min-width: 120px; background: #f8f9fa; border-radius: 12px; padding: 12px; text-align: center; }}
        .score-value {{ font-size: 28px; font-weight: bold; }}
        .score-label {{ color: #6c757d; }}
        .good {{ color: #2b9348; }}
        .medium {{ color: #e9a23b; }}
        .bad {{ color: #d00000; }}
        .problems-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .problems-table th, .problems-table td {{ border: 1px solid #dee2e6; padding: 8px 12px; text-align: left; vertical-align: top; }}
        .problems-table th {{ background: #e9ecef; }}
        .recommendation {{ background: #e3f2fd; border-left: 4px solid #0d6efd; padding: 12px; margin: 10px 0; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
        .badge-perf {{ background: #2b9348; color: white; }}
        .badge-eco {{ background: #118ab2; color: white; }}
        footer {{ text-align: center; margin-top: 40px; color: #6c757d; }}
        button.toggle-all {{ background: #0d6efd; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; margin-bottom: 20px; }}
    </style>
    <script>
        function togglePage(id) {{
            let el = document.getElementById('content-' + id);
            el.classList.toggle('open');
        }}
        function toggleAll() {{
            let contents = document.querySelectorAll('.page-content');
            let anyClosed = Array.from(contents).some(c => !c.classList.contains('open'));
            contents.forEach(c => {{
                if (anyClosed) c.classList.add('open');
                else c.classList.remove('open');
            }});
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
                <div class="page-header" onclick="togglePage({idx})">
                    <h3>⚠️ {file_path}</h3>
                </div>
                <div class="page-content" id="content-{idx}">
                    <p>Erreur lors de l'analyse Lighthouse. Vérifiez que le fichier est valide.</p>
                </div>
            </div>
            """
            continue
        
        scores = data["scores"]
        metrics = data["metrics"]
        top_problems = data["top_problems"]
        
        # Classe CSS pour la couleur du score performance
        perf_class = "good" if scores["performance"] >= 90 else "medium" if scores["performance"] >= 50 else "bad"
        
        html += f"""
        <div class="page-card">
            <div class="page-header" onclick="togglePage({idx})">
                <h3>📄 {file_path}</h3>
            </div>
            <div class="page-content" id="content-{idx}">
                <div class="score-grid">
                    <div class="score-card"><div class="score-value {perf_class}">{scores['performance']:.1f}</div><div class="score-label">Performance</div></div>
                    <div class="score-card"><div class="score-value { 'good' if scores['accessibility']>=90 else 'medium' }">{scores['accessibility']:.1f}</div><div class="score-label">Accessibilité</div></div>
                    <div class="score-card"><div class="score-value { 'good' if scores['best_practices']>=90 else 'medium' }">{scores['best_practices']:.1f}</div><div class="score-label">Bonnes pratiques</div></div>
                    <div class="score-card"><div class="score-value { 'good' if scores['seo']>=90 else 'medium' }">{scores['seo']:.1f}</div><div class="score-label">SEO</div></div>
                </div>
                <div class="recommendation">
                    <strong>📊 Métriques clés :</strong> Poids total {metrics['total_byte_weight']:.0f} Ko | FCP {metrics['first_contentful_paint']:.2f}s | LCP {metrics['largest_contentful_paint']:.2f}s | TBT {metrics['total_blocking_time']:.0f} ms | CLS {metrics['cumulative_layout_shift']:.3f}
                </div>
                <h4>🔝 Top 5 des problèmes à corriger (éco-conception & performance)</h4>
                <table class="problems-table">
                    <thead><tr><th>#</th><th>Audit</th><th>Description</th><th>Score</th><th>Recommandation</th></tr></thead>
                    <tbody>
        """
        # Générer des recommandations basées sur l'ID de l'audit
        for i, problem in enumerate(top_problems, 1):
            rec = recommandation_for_audit(problem["id"])
            html += f"""
                <tr>
                    <td>{i}</td>
                    <td><strong>{problem['title']}</strong></td>
                    <td>{problem['description']}</td>
                    <td style="color:red">{problem['score']:.0f}/100</td>
                    <td>{rec}</td>
                </tr>
            """
        html += """
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    html += """
    <footer>
        <p>🔍 Audit réalisé avec Lighthouse (Chrome Headless). Les scores sont compris entre 0 et 100, un score > 90 est excellent.<br>
        💡 Pour améliorer l'éco-conception : réduisez le poids des ressources, lazy loading, polices système, cache, suppression de JS inutile.</p>
    </footer>
</div>
</body>
</html>
"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Rapport généré : {output_file}")

def recommandation_for_audit(audit_id):
    """Retourne une recommandation personnalisée pour un audit Lighthouse courant."""
    recos = {
        "unminified-css": "Minifiez tous vos fichiers CSS (ex: avec cssnano, ou via build tool).",
        "unminified-javascript": "Minifiez vos JS (Terser, esbuild). Cela réduit le poids et le temps de parsing.",
        "uses-optimized-images": "Utilisez des formats modernes (WebP, AVIF) et compressez vos images (Squoosh, imagemin).",
        "offscreen-images": "Ajoutez loading='lazy' à toutes les images hors viewport.",
        "render-blocking-resources": "Déplacez les scripts vers la fin du body avec 'defer' ou 'async', et inlinez le CSS critique.",
        "uses-rel-preconnect": "Ajoutez <link rel='preconnect'> pour les domaines tiers critiques.",
        "uses-text-compression": "Activez la compression gzip/brotli sur votre serveur (Apache/Nginx).",
        "modern-image-formats": "Servez des images en WebP ou AVIF avec la balise <picture>.",
        "uses-passive-event-listeners": "Marquez vos écouteurs d'événements comme passifs pour améliorer le défilement.",
        "dom-size": "Réduisez la taille du DOM (moins de 1500 nœuds). Utilisez la pagination ou le virtual scrolling.",
        "total-byte-weight": "Éliminez les ressources inutiles, splittez le code, lazy load des bundles.",
        "first-contentful-paint": "Optimisez le chemin critique : inline CSS, réduisez les requêtes bloquantes.",
        "largest-contentful-paint": "Optimisez l'image LCP (preload, serveur rapide, évitez les redirections).",
        "cumulative-layout-shift": "Spécifiez width/height sur toutes les images et vidéos, réservez l'espace des pubs.",
        "uses-responsive-images": "Utilisez srcset avec plusieurs résolutions pour adapter aux écrans.",
        "efficient-animated-content": "Remplacez les GIFs par des vidéos MP4 ou utilisez du CSS/WebP animé.",
        "uses-webp-images": "Convertissez toutes les images raster en WebP (perte ou sans perte).",
        "no-document-write": "Évitez document.write() ; utilisez createElement et appendChild.",
        "no-vulnerable-libraries": "Mettez à jour vos bibliothèques JS/CSS (audit avec npm audit).",
        "js-libraries": "Remplacez les grosses librairies (jQuery, moment) par des alternatives légères ou vanilla JS.",
    }
    # Recherche par correspondance partielle
    for key, rec in recos.items():
        if key in audit_id:
            return rec
    return "Consultez la documentation Lighthouse pour corriger cet audit. (Améliore l'empreinte carbone et les performances)."

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyse batch Lighthouse d'un répertoire HTML")
    parser.add_argument("directory", nargs="?", default=".", help="Répertoire contenant les fichiers HTML (défaut: courant)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port du serveur HTTP local")
    parser.add_argument("--output", default=REPORT_OUTPUT, help="Nom du fichier rapport HTML")
    args = parser.parse_args()
    
    target_dir = os.path.abspath(args.directory)
    if not os.path.isdir(target_dir):
        print(f"❌ Le répertoire {target_dir} n'existe pas.")
        sys.exit(1)
    
    html_files = find_html_files(target_dir)
    if not html_files:
        print(f"Aucun fichier HTML trouvé dans {target_dir}")
        sys.exit(0)
    
    print(f"🔍 {len(html_files)} fichier(s) HTML trouvé(s). Démarrage du serveur HTTP...")
    # Démarrer le serveur HTTP à la racine du répertoire cible
    httpd = start_http_server(target_dir, args.port)
    
    results = {}
    try:
        for full_path, rel_path in html_files:
            url = f"http://localhost:{args.port}/{rel_path.replace(os.sep, '/')}"
            print(f"\n🚀 Analyse de {rel_path} -> {url}")
            # Nom de sortie temporaire
            safe_name = rel_path.replace(os.sep, "_").replace(".html", "").replace(".htm", "")
            output_prefix = os.path.join(os.path.dirname(__file__), f"temp_lh_{safe_name}")
            data, json_path, html_path = run_lighthouse(url, output_prefix)
            if data:
                extracted = extract_metrics_and_audits(data)
                results[rel_path] = extracted
                # Nettoyage des fichiers temporaires
                for f in [f"{output_prefix}.report.json", f"{output_prefix}.report.html"]:
                    if os.path.exists(f):
                        os.remove(f)
            else:
                results[rel_path] = None
    finally:
        # Arrêter le serveur HTTP
        httpd.shutdown()
        print("\n🛑 Serveur HTTP arrêté.")
    
    # Génération du rapport global
    generate_html_report(results, args.output)
    webbrowser.open(f"file://{os.path.abspath(args.output)}")
    print(f"📊 Rapport ouvert dans votre navigateur.")

if __name__ == "__main__":
    main()
```

---

## 🚀 Utilisation

1. **Prérequis**  
   - Node.js et Lighthouse installé globalement :  
     ```bash
     npm install -g lighthouse
     ```
   - Python 3.8+

2. **Placez le script** dans le répertoire parent contenant vos sous-dossiers de pages HTML (ou dans le répertoire à analyser).

3. **Exécutez**  
   ```bash
   python batch_lighthouse_eco.py /chemin/vers/mon_dossier
   ```
   Si vous êtes déjà dans le dossier contenant les fichiers `.html` :
   ```bash
   python batch_lighthouse_eco.py .
   ```

4. **Le script** :  
   - Lance un serveur HTTP local sur le port `8888` (modifiable avec `--port`).  
   - Parcourt **tous les sous-dossiers** récursivement.  
   - Pour chaque fichier `.html`, lance Lighthouse (mode desktop).  
   - Extrait les scores (Performance, Accessibilité, Bonnes pratiques, SEO) et les métriques (poids, FCP, LCP, TBT, CLS).  
   - Identifie les 5 audits les plus problématiques (score < 0.9).  
   - Génère un **rapport HTML cliquable** avec un tableau détaillé et des recommandations sur mesure.

5. **Rapport généré** : `eco_batch_report.html` (ouvert automatiquement).

---

## 📝 Exemple de sortie

Le rapport HTML contient pour chaque page :

- **Scores** sous forme de tuiles colorées  
- **Métriques techniques**  
- **Tableau des 5 pires problèmes** avec :
  - Nom de l’audit (ex: "Unminified CSS")
  - Description détaillée
  - Score partiel
  - **Recommandation concrète** pour corriger (ex: "Minifiez vos fichiers CSS avec cssnano")

---

## ⚙️ Personnalisation

- Pour changer le seuil des problèmes (actuellement < 0.9), modifiez la ligne `if score is not None and score < 0.9` dans `extract_metrics_and_audits`.
- Pour ajouter d’autres métriques (ex: ecoIndex, nombre de requêtes), enrichissez la fonction `extract_metrics_and_audits` en lisant les audits correspondants.

---

Ce script vous permet d’auditer en masse l’état de l’éco-conception de tous vos projets HTML, d’identifier rapidement les pages les plus énergivores et de fournir aux développeurs des correctifs précis. 🌱
