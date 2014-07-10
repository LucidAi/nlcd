# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from husky.extraction import NerExtractor

from husky.fetchers import PageFetcher
from husky.api.google import CseAPI

from husky.extraction.google import get_extractor

from client.api.decorators import nlcd_api_call
from husky.textutil import TextUtil


@csrf_exempt
@nlcd_api_call
def get_article(request):
    url = request.GET.get("url")
    text = PageFetcher().fetch_document_text(url)
    preproc = TextUtil()
    text = "\n".join([str(s) for s in preproc.sent_tokenize(text)])
    return {
        "url": url,
        "text": text,
    }


@csrf_exempt
@nlcd_api_call
def get_segments(request):
    text = request.GET.get("text")
    preproc = TextUtil()
    sentences = list(set(preproc.sent_tokenize(text)))
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

    rel_sets = []

    for entry in related:
        text = entry["text"].encode("utf-8")
        entry_query = cse.make_query(query_string=text, exact_terms=text)
        found_documents = list(cse.find_results(entry_query, max_results=100))
        rel_sets.append((
            {
                "id": entry["id"],
                "type": "relations.SegmentText",
                "text": entry["text"],
                "query": entry_query,
            },
            found_documents,
        ))

    # with open("webapp/json/results.json", "rb") as fl:
    #     related = json.load(fl)["results"]

    nlcd_annotated = []

    for relation, found_documents in rel_sets:
        annotated_documents = []
        nlcd_annotated.append({
            "relation": relation,
            "documents": annotated_documents,
        })
        for entry in found_documents:
            urls = doc_extractor.extract_urls(entry)
            authors = doc_extractor.extract_authors(entry)
            sources = doc_extractor.extract_sources(entry)
            titles = doc_extractor.extract_titles(entry)
            pub_dates = doc_extractor.extract_publish_dates(entry)
            annotated_documents.append({
                "googleAnnotation": entry,
                "nlcdAnnotation": {
                    "url": entry.get("link"),
                    "cacheId": entry.get("cacheId"),
                    "matchedEntities": {
                        "urls": urls,
                        "authors": authors,
                        "sources": sources,
                        "titles": titles,
                        "publishedDates": pub_dates,
                    },
                    "nerEntities": {
                        "sources": ner_extractor.extract_entities(sources, set_label="ORG"),
                        "authors": ner_extractor.extract_entities(authors, set_label="PER")
                    },
                }
            })

    return {
        "related": nlcd_annotated,
    }

@csrf_exempt
@nlcd_api_call
def fetch_related(request):
    import lz4
    # query = json.loads(request.POST.get("query"))


    query = json.loads(lz4.decompress(request.body))





    return {
        "response": "success",
    }
