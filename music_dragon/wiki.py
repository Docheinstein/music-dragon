from typing import Sequence

import requests
from PyQt5.QtCore import pyqtSignal
from wikidata.client import Client as WikidataClient
from wikidata.commonsmedia import File as WikidataFile
from wikidata.entity import EntityId

from music_dragon import workers
from music_dragon.log import debug
from music_dragon.workers import Worker

WIKIDATA_IMAGE_PROPERTY = EntityId("P18")
WIKIDATA_LOGO_PROPERTY = EntityId("P154")

# ======== FETCH IMAGE =======
# Fetch wikidata image
# ============================

class FetchWikidataImageWorker(Worker):
    result = pyqtSignal(str, bytes, str)

    def __init__(self, wiki_id, user_data=None):
        super().__init__()
        self.wiki_id = wiki_id
        self.user_data = user_data

    def run(self) -> None:
        debug(f"WIKIDATA: get: '{self.wiki_id}'")

        wiki = WikidataClient()
        entity = wiki.get(self.wiki_id, load=True)
        best_image = None
        try:
            logo_prop = wiki.get(WIKIDATA_LOGO_PROPERTY) # logo
            logos: Sequence[WikidataFile] = entity.getlist(logo_prop)
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
                images: Sequence[WikidataFile] = entity.getlist(image_prop)
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
            self.result.emit(self.wiki_id, result, self.user_data)
        else:
            print("WARN: image not found")
            self.result.emit(self.wiki_id, bytes(), self.user_data)


def fetch_wikidata_image(wiki_id, callback, user_data=None, priority=workers.Worker.PRIORITY_NORMAL):
    worker = FetchWikidataImageWorker(wiki_id, user_data)
    worker.priority = priority
    worker.result.connect(callback)
    workers.schedule(worker)