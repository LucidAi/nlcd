# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import json
import traceback

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from textblob import TextBlob
from fenrir.fetcher import Fetcher
from fenrir.api.google import CseAPI


@csrf_exempt
def get_article(request):

    try:
        url = request.GET.get("url")
        text = Fetcher().fetch_document_text(url)
        text = re.sub("\&#?[a-z0-9]+;", "", text)
        blob = TextBlob(text)
        text = "\n".join([str(s) for s in blob.sentences])
    except:
        traceback.print_exc()

    return HttpResponse(json.dumps({
        "url": url,
        "text": text,
    }), content_type="application/json")


@csrf_exempt
def get_segments(request):
    try:
        text = request.GET.get("text")
        blob = TextBlob(text)
        sentences = [str(s) for s in blob.sentences]
        quoted = []
        for sent in sentences:
            s_quoted = re.findall('\"([^"]*)\"', sent) \
                     + re.findall('\'([^"]*)\'', sent) \
                     + re.findall('“([^"]*)”', sent)
            quoted.extend(s_quoted)

        all_segments = list(set(sentences + quoted))
        filtered = []
        for s_id, segment in enumerate(all_segments):
            text = segment.decode("utf-8")
            tokens = [t.lower() for t in TextBlob(text).tokens]
            tk_size = len(tokens)
            tx_size = len(text)
            is_important = tk_size >= 4 and tk_size <= 30
            filtered.append({
                "id": s_id,
                "text": text,
                "tokens": tokens,
                "tk_size": tk_size,
                "tx_size": tx_size,
                "is_important": is_important
            })
    except:
        traceback.print_exc()

    return HttpResponse(json.dumps({
            "sentences": sentences,
            "quoted": quoted,
            "filtered": filtered,
        }, sort_keys=True), content_type="application/json")


@csrf_exempt
def find_related(request):
    try:

        api = settings.CONF["nlcd"]["searchApi"][0]
        cse = CseAPI(api["googleApiKey"], api["googleEngineId"])
        related = json.loads(request.GET.get("segments"))
        results = []

        for entry in related:

            entry_query = cse.make_query(query_string=entry["text"])
            found_documents = list(cse.find_results(entry_query))

            results.append({

                "relation": {
                    "id": entry["id"],
                    "type": "relations.SegmentText",
                    "text": entry["text"],
                    "query": entry_query,
                },

                "foundDocuments": found_documents,

            })


        return HttpResponse(json.dumps({

            "results": results,

        }, sort_keys=True), content_type="application/json")


    except:
        traceback.print_exc()



