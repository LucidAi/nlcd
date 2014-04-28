# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from fenrir.fetcher import Fetcher
from fenrir.api.google import CseAPI

from fenrir.extraction.entity import NerExtractor
from fenrir.extraction.pattern import get_extractor
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
    sentences = list(set(preproc.sent_segmentize(text)))
    quoted = list(set(preproc.extract_quoted(sentences)))
    all_segments = sentences + quoted
    filtered = preproc.filter_sents(sentences, 4, 30)
    return {
        "sentences": sentences,
        "quoted":    quoted,
        "filtered":  filtered,
    }


@csrf_exempt
@nlcd_api_call
def find_related(request):
    api = settings.CONF["nlcd"]["searchApi"][0]
    cse = CseAPI(api["googleApiKey"], api["googleEngineId"])
    doc_extractor = get_extractor(api["id"])
    ner_extractor = NerExtractor()
    related = json.loads(request.GET.get("segments"))
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
        related = json.load(fl)["results"]

    results = []
    for rel_set in related:
        for entry in rel_set["foundDocuments"]:
            urls = doc_extractor.extract_urls(entry)
            authors = doc_extractor.extract_authors(entry)
            sources = doc_extractor.extract_sources(entry)
            titles = doc_extractor.extract_titles(entry)
            pub_dates = doc_extractor.extract_publish_dates(entry)
            results.append({
                "nlcdAnnotation": {
                    "url": entry.get("formattedUrl"),
                    "cacheId": entry.get("cacheId"),
                    "matchedEntities": {
                        "urls": urls,
                        "authors": authors,
                        "sources": sources,
                        "titles": titles,
                        "publishedDates": pub_dates,
                    },
                    "nerEntities": {
                        "sources": ner_extractor.extract_entities(sources, set_label=None),
                        "authors": ner_extractor.extract_entities(authors, set_label=None)
                    },
                }
            })

    return {
        "related": results,
    }
