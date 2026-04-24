
# 🌿 Éco-conception Web – Kit pédagogique complet

Ce projet fournit un environnement d’apprentissage et d’audit pour enseigner les **bonnes pratiques d’éco-conception web** aux développeurs. Il contient :

- Deux pages HTML contrastées :
  - `bonne-page.html` : page respectant le **Top 40 des bonnes pratiques** (performante, légère, accessible)
  - `mauvaise-page.html` : page volontairement non optimisée (lourde, lente, énergivore)
- Un script Python `lighthouse_eco_eval.py` pour comparer ces deux pages via Lighthouse.
- Un script `batch_lighthouse_eco.py` pour **analyser tous les fichiers HTML d’un répertoire** et générer un rapport détaillé avec le **top 5 des problèmes** et des recommandations.

L’objectif est de montrer concrètement l’impact du code sur les performances, l’empreinte carbone et les scores Lighthouse, et de fournir des outils automatisés pour diagnostiquer et améliorer n’importe quel site.

---

## 📦 Prérequis

- **Node.js** (v14 ou supérieure) et **Lighthouse** installé globalement :
  ```bash
  npm install -g lighthouse
  ```
- **Python 3.8+** (aucune bibliothèque externe requise, uniquement la stdlib)

---

## 📁 Structure des fichiers

```
projet-eco-conception/
├── ecoconceptionpage.html               # Page exemplaire éco-conçue
├── mauvaisepage.html            # Page anti-éco-conception (volontairement mauvaise)
├── lighthouse_eco_eval.py        # Script d'évaluation unitaire (comparaison 1 page vs 1 autre)
├── batch_lighthouse_eco.py       # Script d'analyse batch (dossier entier)
└── README.md
```

*(Les rapports générés apparaîtront dans le dossier courant ou dans `lighthouse_reports/`)*

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
- Génère un résumé texte `eco_audit_summary.txt`

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

### `bonne-page.html` – 40 bonnes practices appliquées

- ✅ Images au format WebP + `loading="lazy"` + dimensions explicites (CLS maîtrisé)
- ✅ CSS chargé de manière non bloquante (media + onload)
- ✅ Préconnexions (`preconnect`, `dns-prefetch`) aux CDN
- ✅ Pas de polices externes (polices système)
- ✅ Scripts en `defer`
- ✅ DOM léger (< 800 nœuds)
- ✅ Pas de tracking tiers, pas de carrousel inutile
- ✅ Respect de `prefers-reduced-motion`
- ✅ Compression et cache HTTP (à configurer côté serveur)

### `mauvaise-page.html` – Exemple de ce qu’il ne faut pas faire

- ❌ Polices Google + FontAwesome (requêtes supplémentaires)
- ❌ Images sans lazy loading, sans dimensions, sans WebP
- ❌ Scripts bloquants en `head`
- ❌ jQuery inutile + boucles lourdes
- ❌ SetInterval non nettoyé, écouteur `scroll` sans throttling
- ❌ Iframe météo externe
- ❌ DOM surchargé (200 éléments générés dynamiquement)
- ❌ Tracking Analytics + Hotjar, pixel tiers

Cette page est un excellent support pour **montrer les erreurs** avant de les corriger.

---

## 📊 Interprétation des résultats Lighthouse

| Métrique | Bonne pratique | Mauvaise pratique | Impact éco-conception |
|----------|----------------|-------------------|------------------------|
| Performance | > 90 | < 30 | Influence directement la consommation CPU et la durée de chargement |
| Total Byte Weight | < 500 Ko | > 2 Mo | Plus de données = plus d’énergie réseau et serveur |
| CLS | < 0,1 | > 0,25 | Évite les déplacements de contenu (réduit la frustration et le recalcul CSS) |
| TBT | < 150 ms | > 500 ms | Moins de JavaScript = batterie économisée |

---

## 🛠️ Personnalisation avancée

### Modifier les seuils des problèmes (batch)

Dans `batch_lighthouse_eco.py`, cherchez la ligne :

```python
if score is not None and score < 0.9
```

Remplacez `0.9` par le seuil désiré (ex. `0.75` pour n’inclure que les très mauvais audits).

### Ajouter une métrique (ex. ecoIndex)

Lighthouse ne fournit pas nativement l’ecoIndex. Vous pouvez enrichir le script en appelant une API externe (ex. GreenIT Analysis) ou en utilisant la librairie `co2.js`. Pour aller plus loin, intégrez l’outil [Ecoindex CLI](https://github.com/cnumr/ecoindex_cli).

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

