# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from fenrir.fetcher import Fetcher
from fenrir.api.google import CseAPI
from fenrir.extraction.base import TextPreprocessor

from client.api.decorators import nlcd_api_call


@csrf_exempt
@nlcd_api_call
def get_article(request):
    url = request.GET.get("url")
    text = Fetcher().fetch_document_text(url)
    preproc = TextPreprocessor()
    text = "\n".join([str(s) for s in preproc.sent_segmentize(text)])
    return {
        "url": url,
        "text": text,
    }


@csrf_exempt
@nlcd_api_call
def get_segments(request):
    text = request.GET.get("text")
    preproc = TextPreprocessor()
    sentences = preproc.sent_segmentize(text)
    quoted = preproc.extract_quoted(sentences)
    all_segments = sentences + quoted
    filtered = preproc.filter_sents(sentences, 4, 30)
    return {
        "sentences": sentences,
        "quoted":    quoted,
        "filtered":  filtered,
    }


@csrf_exempt
def find_related(request):
    try:

        api = settings.CONF["nlcd"]["searchApi"][0]
        cse = CseAPI(api["googleApiKey"], api["googleEngineId"])
        related = json.loads(request.GET.get("segments"))
        results = []

        # for entry in related:
        #     entry_query = cse.make_query(query_string=entry["text"].encode('utf-8'))
        #     found_documents = list(cse.find_results(entry_query, number=30))
        #     results.append({
        #         "relation": {
        #             "id": entry["id"],
        #             "type": "relations.SegmentText",
        #             "text": entry["text"],
        #             "query": entry_query,
        #         },
        #         "foundDocuments": found_documents,
        #     })

        with open("webapp/json/results.json", "rb") as fl:
            results = json.load(fl)["results"]

        for relSet in results:

            for entry in relSet["foundDocuments"]:

                author = []
                source = []
                urls   = []

                try: source.append(entry["pagemap"]["NewsItem"][0]["site_name"])
                except: pass
                try: source.append(entry["pagemap"]["metatags"][0]["og:site_name"])
                except: pass
                try: source.append(entry["pagemap"]["metatags"][0]["source"])
                except: pass
                try: source.append(entry["displayLink"])
                except: pass

                try: author.append(entry["pagemap"]["metatags"][0]["author"])
                except: pass
                try: author.append(entry["pagemap"]["metatags"][0]["dc.creator"])
                except: pass

                urls.append(entry["link"])

                entry["nlcdMeta"] = {
                    "author": list(set(author)),
                    "source": list(set(source)),
                    "urls":   urls,
                }



        return HttpResponse(json.dumps({

            "results": results,

        }, sort_keys=True), content_type="application/json")


    except:
        traceback.print_exc()



