# GreenITStarter
Green IT Starter

* Numérque 4%  impact C02

## Impact 3 Axes :   Climat / Biodiversité / Ressources(mineraux, sol, eau)

- Preserver l'environnement

## 9  Seuils à ne pas depasser

- 6 /9 ont été depassé.

##  ACV(Analyse du Cycle de Vie),  norme ISO

- Fabrication : 80% (impact)
- Utilisation: 15%
- Fin de Vie: 5%
  
##  Starter 

1) Vous pouvez accéder aux 115 bonnes pratiques de l’éco-conception web à l’adresse suivante : https://github.com/cnumr/best-practices. Nous utiliserons cette ressources demain ensemble, mais vous pouvez déjà commencer à la lire si vous le désirez.

  Fork:  https://github.com/sanogotech/best-practicesEcoDesignGreenIT

2) Veuillez également télécharger l’extension web GreenIT analysis en suivant les instruction ci-dessous : 
Installer Plugin Ecoindex :
Aller sur cette page : https://collectif.greenit.fr/outils.html 
Dans « GreenIT-Analysis - Calcul automatique d'un EcoIndex + Ecometer – extension », cliquer sur « Installer l'extension EcoIndex pour Firefox/Chrome »
Cliquer sur « Ajouter »

Via Chrome :  
- https://chromewebstore.google.com/detail/ecoindexfr/apeadjelacokohnkfclnhjlihklpclmp?pli=1

**Utiliser Ecoindex :**

Faire F12 ou Fn + F12
Cliquer sur « GreenIT »
Cliquer sur « Vider le cache navigateur », « Activer l'analyse des bonnes pratiques » puis sur « Lancer l’analyse »
Cliquer sur « Sauver l’analyse »

## Pythhon Install
```
pip install ecoindex-scraper
nstall setuptools in your machine

pip install setuptools
```

**Get a page analysis**

You can run a page analysis by calling the function get_page_analysis():

(function) get_page_analysis: (url: HttpUrl, window_size: WindowSize | None = WindowSize(width=1920, height=1080), wait_before_scroll: int | None = 1, wait_after_scroll: int | None = 1) -> Coroutine[Any, Any, Result]
Example:

```
import asyncio
from pprint import pprint

from ecoindex_scraper.scrap import EcoindexScraper

pprint(
    asyncio.run(
        EcoindexScraper(url="http://ecoindex.fr")
        .init_chromedriver()
        .get_page_analysis()
    )
)
```

**Result example:**

Result(width=1920, height=1080, url=HttpUrl('http://ecoindex.fr', ), size=549.253, nodes=52, requests=12, grade='A', score=90.0, ges=1.2, water=1.8, ecoindex_version='5.0.0', date=datetime.datetime(2022, 9, 12, 10, 54, 46, 773443), page_type=None)
Default behaviour: By default, the page analysis simulates:

Uses the last version of chrome (can be set with parameter chrome_version_main to a given version. IE 107)
Window size of 1920x1080 pixels (can be set with parameter window_size)
Wait for 1 second when page is loaded (can be set with parameter wait_before_scroll)
Scroll to the bottom of the page (if it is possible)
Wait for 1 second after having scrolled to the bottom of the page (can be set with parameter wait_after_scroll)
Get a page analysis and generate a screenshot
It is possible to generate a screenshot of the analyzed page by adding a ScreenShot property to the EcoindexScraper object. You have to define an id (can be a string, but it is recommended to use a unique id) and a path to the screenshot file (if the folder does not exist, it will be created).

```
import asyncio
from pprint import pprint
from uuid import uuid1

from ecoindex.models import ScreenShot
from ecoindex_scraper.scrap import EcoindexScraper

pprint(
    asyncio.run(
        EcoindexScraper(
            url="http://www.ecoindex.fr/",
            screenshot=ScreenShot(id=str(uuid1()), folder="./screenshots"),
        )
        .init_chromedriver()
        .get_page_analysis()
    )
)
```

**Async analysis**

You can also run the analysis asynchronously:

```
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from ecoindex_scraper.scrap import EcoindexScraper

def run_page_analysis(url):
    return asyncio.run(
        EcoindexScraper(url=url)
        .init_chromedriver()
        .get_page_analysis()
    )


with ThreadPoolExecutor(max_workers=8) as executor:
    future_to_analysis = {}

    url = "https://www.ecoindex.fr"

    for i in range(10):
        future_to_analysis[
            executor.submit(
                run_page_analysis,
                url,
            )
        ] = (url)

    for future in as_completed(future_to_analysis):
        try:
            print(future.result())
        except Exception as e:
            print(e)

```

Note: In this case, it is highly recommanded to use a fixed chromedriver version. You can set it with the parameter chrome_version_main (IE 107) and driver_executable_path (IE /usr/bin/chromedriver). Otherwise undected-chromedriver will download the latest version of chromedriver and patch it for each analysis.
