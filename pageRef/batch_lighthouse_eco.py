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

    # Flags Chrome indispensables sous Windows pour éviter EPERM
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
                # Nettoyage des fichiers temporaires
                for f in [f"{output_prefix}.report.json", f"{output_prefix}.report.html"]:
                    if os.path.exists(f):
                        os.remove(f)
            else:
                results[rel_path] = None
            # Pause pour éviter les conflits sur le dossier temporaire Windows
            time.sleep(1)
    finally:
        httpd.shutdown()
        print("\n🛑 Serveur HTTP arrêté.")

    generate_html_report(results, args.output)
    webbrowser.open(f"file://{os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()