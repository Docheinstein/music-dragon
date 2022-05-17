from typing import Any

from wikidata.client import Client as WikidataClient
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, pyqtSlot, QThreadPool

from log import debug
import requests

WIKIDATA_IMAGE_PROPERTY = "P18"
WIKIDATA_LOGO_PROPERTY = "P154"

# ======== FETCH IMAGE =======
# Fetch wikidata image
# ============================

class FetchWikidataImageSignals(QObject):
    finished = pyqtSignal(str, bytes, str)

class FetchWikidataImageRunnable(QRunnable):
    def __init__(self, wiki_id, user_data=None):
        super().__init__()
        self.signals = FetchWikidataImageSignals()
        self.wiki_id = wiki_id
        self.user_data = user_data

    @pyqtSlot()
    def run(self) -> None:
        debug(f"[FetchWikidataImageRunnable (wiki_id='{self.wiki_id}']")

        debug(f"WIKIDATA: get: '{self.wiki_id}'")

        wiki = WikidataClient()
        entity = wiki.get(self.wiki_id, load=True)
        best_image = None
        try:
            logo_prop = wiki.get(WIKIDATA_LOGO_PROPERTY) # logo
            logos = entity.getlist(logo_prop)
            if logos:
                debug("Has logos")
                for logo in logos:
                    debug(f"Found logo: {logo.image_resolution} '{logo.image_url}'")
                    if ".svg" not in  logo.image_url:
                        if not best_image or logo.image_resolution < best_image.image_resolution:
                            best_image = logo
                        else:
                            debug("Skipping since size is greater than current one")
                    else:
                        debug("Skipping since .svg")

        except:
            pass
        if best_image is None:
            try:
                image_prop = wiki.get(WIKIDATA_IMAGE_PROPERTY) # image
                images = entity.getlist(image_prop)
                if images:
                    debug("Has images")
                    for image in images:
                        debug(f"Found image: {image.image_resolution}'{image.image_url}'")
                        if ".svg" not in image.image_url:
                            if not best_image or image.image_resolution < best_image.image_resolution:
                                best_image = image
                            else:
                                debug("Skipping since size is greater than current one")
                        else:
                            debug("Skipping since .svg")
            except:
                pass
        if best_image is not None:
            debug(f"Image will be retrieved from {best_image.image_url}")
            result = requests.get(best_image.image_url, headers={
                "User-Agent": "MusicDragonBot/1.0 (docheinstein@gmail.com) MusicDragon/1.0",
            }).content
            debug(f"Retrieved image data size: {len(result)}")
            self.signals.finished.emit(self.wiki_id, result, self.user_data)
        else:
            print("WARN: image not found")



def fetch_wikidata_image(wiki_id, callback, user_data=None):
    debug(f"fetch_wikidata_image(wiki_id={wiki_id})")

    runnable = FetchWikidataImageRunnable(wiki_id, user_data)
    runnable.signals.finished.connect(callback)
    QThreadPool.globalInstance().start(runnable)


