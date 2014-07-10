#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import os
import lz4
import csv
import sys
import json
import logging
import argparse
import datetime
import collections

import husky.db
import husky.dicts
import husky.evaluation
import husky.api.google

from husky.fetchers import PageFetcher

from husky.extraction import EntityExtractor
from husky.extraction import EntityNormalizer

from husky.rd import ReferenceEntry
from husky.rd import ReferenceIndex


from husky.textutil import TextUtil


ORIGIN_URL_FILE                 = "1.origin_url"
ORIGIN_HTML_DIR                 = "2.origin_html"
ORIGIN_BODY_DIR                 = "3.origin_body"
ORIGIN_SEGMENT_DIR              = "4.origin_segm"
ORIGIN_GSE_DIR                  = "5.origin_gse"
RELATED_GSE_ANNOTATIONS_DIR     = "6.related.gse"
RELATED_FULL_DATA_DIR           = "7.related.data"
RELATED_FULL_ANNOTATIONS_DIR    = "8.related.annot"
NORMALIZED_ANNOTATIONS_DIR      = "9.norm.annot"
EVALUATION_DATA_DIR             = "10.evaluation.data"
CROSS_REF_DIR                   = "11.crosref.data"
CROSS_REF_OUT_DIR               = "12.crosref.out"


def clean_directory(path):
    """
    Create path if not exist otherwise recreates it.
    """
    if os.path.exists(path):
        os.system("rm -rf %s" % path)
    os.mkdir(path)


def to_utf_8_dict(data):
    """
    Encode dict into 'JSON-friendly' utf-8 format.
    """
    if isinstance(data, basestring):
        return data.encode("utf-8")
    elif isinstance(data, collections.Mapping):
        return dict(map(to_utf_8_dict, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(to_utf_8_dict, data))
    else:
        return data


def read_origins(args):
    """
    Read origins file and return list of origins urls.
    """
    with open(os.path.join(args.work_dir, ORIGIN_URL_FILE), "rb") as i_fl:
        return i_fl.read().strip("\n").split("\n")


def json_dump(obj, fp, encode=True):
    """
    Write object in JSON format to file stream fp.
    """
    fp.write(json.dumps(to_utf_8_dict(obj) if encode else obj, indent=4, ensure_ascii=not encode))


def step_1_init_work_dir(args):
    """
    Create work directory if not exists and copy origins file there.
    """
    clean_directory(args.work_dir)
    origins_new_fp = os.path.join(args.work_dir, ORIGIN_URL_FILE)

    with open(args.origins_file_path, "rb") as i_fl, open(origins_new_fp, "wb") as o_fl:
        origins = i_fl.read().strip("\n").split("\n")
        o_fl.write("\n".join(origins))

    logging.info("Initialized %d origins." % len(origins))


def step_2_fetch_origin_articles(args):
    """
    Fetch origin articles HTML and save them in work directory.
    """
    origin_html_dir = os.path.join(args.work_dir, ORIGIN_HTML_DIR)
    fetcher = PageFetcher()

    clean_directory(origin_html_dir)

    origins = read_origins(args)
    origin_responses = fetcher.fetch_documents(origins, max_threads=args.max_threads)

    def write_html_to_disk(i_response):

        i, response = i_response
        o_html_fp = os.path.join(origin_html_dir, "%d.html" % i)

        with open(o_html_fp, "wb") as fl:
            fl.write(fetcher.response_to_utf_8(response))

    map(write_html_to_disk, enumerate(origin_responses))

    logging.info("Fetched %d origins." % len(origins))


def step_3_extracting_article_sentences(args):
    """
    Read origin articles from work directory and extract clean text from them.
    """
    origin_html_dir = os.path.join(args.work_dir, ORIGIN_HTML_DIR)
    origin_body_dir = os.path.join(args.work_dir, ORIGIN_BODY_DIR)

    text_util = TextUtil()
    origins = read_origins(args)

    clean_directory(origin_body_dir)

    for i, url in enumerate(origins):

        i_html_fp = os.path.join(origin_html_dir, "%d.html" % i)
        o_body_fp = os.path.join(origin_body_dir, "%d.json" % i)

        with open(i_html_fp, "rb") as i_fl:

            html = i_fl.read()
            body, lang_id = text_util.extract_body(url, html)

            with open(o_body_fp, "wb") as o_fl:
                json_dump({
                    "body": body,
                    "lang_id": lang_id,
                }, o_fl)

    logging.info("Extracted %d bodies." % len(origins))


def step_4_extract_sentences(args):
    """
    Extract sentences and quotes and segment them.
    """
    origin_body_dir = os.path.join(args.work_dir, ORIGIN_BODY_DIR)
    origin_sentence_dir = os.path.join(args.work_dir, ORIGIN_SEGMENT_DIR)
    origins = read_origins(args)

    text_util = TextUtil()

    clean_directory(origin_sentence_dir)

    for i, url in enumerate(origins):

        i_body_fp = os.path.join(origin_body_dir, "%d.json" % i)
        o_segment_fp = os.path.join(origin_sentence_dir, "%d.json" % i)

        with open(i_body_fp, "rb") as i_fl:

            body_obj = json.load(i_fl)

            with open(o_segment_fp, "wb") as o_fl:

                body = body_obj["body"]
                lang_id = body_obj["lang_id"].encode("utf-8")

                sentences = text_util.sent_tokenize(body)
                quoted = text_util.extract_quoted(body)
                segments = text_util.select_segments(sentences, quoted)

                json_dump({
                    "url": url,
                    "text": body,
                    "lang_id": lang_id,
                    "sentences": sentences,
                    "quoted": quoted,
                    "segments": segments,
                }, o_fl)

                logging.info(("Extracted:    %02d sent    %02d quot    %02d segm." % (
                    len(sentences),
                    len(quoted),
                    len(segments)
                )).encode("utf-8"))


def step_5_request_gse(args):

    """
    Filter out non-important sentences and find related pages.
    """

    origin_segment_dir = os.path.join(args.work_dir, ORIGIN_SEGMENT_DIR)
    origin_gse_dir = os.path.join(args.work_dir, ORIGIN_GSE_DIR)
    upper_threshold = args.gse_upper_threshold
    bottom_threshold = args.gse_bottom_threshold
    query_size_heuristic = args.gse_query_size_heuristic

    with open(args.nlcd_conf_file, "rb") as fl:
        nlcd_config = json.load(fl)

    origins = read_origins(args)
    gse_api = husky.api.create_api(nlcd_config["nlcd"]["searchApi"])

    clean_directory(origin_gse_dir)

    for i, url in enumerate(origins):

        i_segment_fp = os.path.join(origin_segment_dir, "%d.json" % i)
        o_gse_fp = os.path.join(origin_gse_dir, "%d.json" % i)
        unique_links = set()

        with open(i_segment_fp, "rb") as i_fl:

            segments = [s.encode("utf-8") for s in json.load(i_fl)["segments"]]
            origin_gse = []

            with open(o_gse_fp, "wb") as o_fl:

                for segment in segments:

                    query = gse_api.make_query(query_string=segment, exact_terms=segment)
                    found, urls, total = gse_api.find_results(query,
                                                              query_size_heuristic=query_size_heuristic,
                                                              upper_threshold=upper_threshold,
                                                              bottom_threshold=bottom_threshold,
                                                              max_results=upper_threshold)

                    for item in found:
                        unique_links.add(item["link"])

                    origin_gse.append({
                        "segment": segment,
                        "totalResults": total,
                        "foundUrls": urls,
                        "foundItems": found
                    })

                    segment_fragment = segment if len(segment) < 16 else segment[:16]
                    logging.info("Found %d items using segment '%s...'" % (total, segment_fragment))

                    # text = segment.replace("\t", " ")
                    # count = total
                    # is_more = int(total > 10)
                    # test_file.write("%s\t%d\t%d\n" % (text, count, is_more))

                logging.info("Saving GSE with %d unique links." % len(unique_links))
                json_dump(origin_gse, o_fl, encode=False)


def step_6_filter_out_unrelated(args):
    """
    Filter not related documents found by Google.
    """


def step_6_extract_search_annotations(args):
    """
    Extract Google searcher annotations.
    """
    origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
    articles_filtered_dir = os.path.join(args.work_dir, ORIGIN_GSE_DIR)
    related_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)
    if os.path.exists(related_annotations_dir):
        logging.info("Cleaning previous related annotations directory %s" % related_annotations_dir)
        rm_cmd = "rm -rf %s" % related_annotations_dir
        os.system(rm_cmd)
    logging.info("Creating related annotations directory: %s" % related_annotations_dir)
    os.mkdir(related_annotations_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    annotations_extractor = AnnotationsExtractor()
    logging.info("Created annotations extractor: %r" % annotations_extractor)
    for i, url in enumerate(origin_urls):
        logging.info("Loading article sentences from (%d): %s" % (i, url))
        filtered_sentences_json_fp = os.path.join(articles_filtered_dir, "%d.json" % i)
        related_annotations_json_fp = os.path.join(related_annotations_dir, "%d.json" % i)
        with open(filtered_sentences_json_fp, "rb") as i_fl:
            article = json.load(i_fl)
            with open(related_annotations_json_fp, "wb") as o_fl:
                # url = article["url"].encode("utf-8")
                # title = article["title"].encode("utf-8")
                # lang_id = article["lang_id"].encode("utf-8")
                filtered_sentences = article["filteredSentences"]
                annotations = {}
                for sentence_entry in filtered_sentences:
                    sent_total_results = sentence_entry["totalResults"]
                    sent_api_response = sentence_entry["apiResponse"]
                    if sent_total_results == 0:
                        continue
                    for related_item in sent_api_response["items"]:
                        annotation = annotations_extractor.annotate(related_item)
                        if annotation.url in annotations:
                            continue
                        annotations[annotation.url] = {
                            "url": annotation.url,
                            "title": annotation.title,
                            "authors": annotation.authors,
                            "source": annotation.sources,
                            "dates": annotation.dates,
                            "images": annotation.images,
                        }
                json.dump(annotations.values(), o_fl, indent=4, sort_keys=False)


def step_7_fetch_related_pages(args):
    """Fetch related pages.
    """
    origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
    related_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)
    related_pages_database_dir = os.path.join(args.work_dir, RELATED_FULL_DATA_DIR)
    if os.path.exists(related_annotations_dir):
        logging.info("Cleaning previous related pages directory %s" % related_pages_database_dir)
        rm_cmd = "rm -rf %s" % related_pages_database_dir
        os.system(rm_cmd)
    logging.info("Creating related pages directory: %s" % related_pages_database_dir)
    os.mkdir(related_pages_database_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    fetcher = husky.fetchers.PageFetcher()
    related_data_ldb = husky.db.create(related_pages_database_dir)
    urls = []
    for i, url in enumerate(origin_urls):
        related_annotations_json_fp = os.path.join(related_annotations_dir, "%d.json" % i)
        logging.info("Loading related annotation from from (%d): %s" % (i, related_annotations_json_fp))
        with open(related_annotations_json_fp, "rb") as i_fl:
            annotations = json.load(i_fl)
            for related_item in annotations:
                url = related_item["url"].encode("utf-8")
                urls.append(url)
                related_data_ldb.put("json+%s" % url, json.dumps(related_item))
    async_related_list = fetcher.fetch_documents(urls, max_threads=args.max_threads)
    def save_html(j_response):
        try:
            j, response = j_response
            if j % 10 == 0 and j > 0:
                logging.info("Added %d/%d." % (len(urls), j+1))
            html = fetcher.response_to_utf_8(response)
            if args.use_compression == 1:
                html = lz4.compressHC(html)
            if response.history is not None and len(response.history) > 0:
                url = response.history[0].url.encode("utf-8")
            else:
                url = response.url.encode("utf-8")
        except Exception:
            return
        related_data_ldb.put("html+%s" % url, html)
    map(save_html, enumerate(async_related_list))
    related_data_ldb.close()
    logging.info("Added %d/%d." % (len(urls), len(urls)))
    logging.info("Fetching completed.")


def step_8_extract_full_annotations(args):
    """Extract full annotations from related pages HTML.
    """
    origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
    related_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)
    related_pages_dir = os.path.join(args.work_dir, RELATED_FULL_DATA_DIR)
    related_full_annotations_dir = os.path.join(args.work_dir, RELATED_FULL_ANNOTATIONS_DIR)
    if os.path.exists(related_full_annotations_dir):
        logging.info("Cleaning previous full annotations directory %s" % related_full_annotations_dir)
        rm_cmd = "rm -rf %s" % related_full_annotations_dir
        os.system(rm_cmd)
    logging.info("Creating full annotations directory: %s" % related_full_annotations_dir)
    os.mkdir(related_full_annotations_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    annotator = EntityExtractor()
    annotations_cache = {}
    for i, url in enumerate(origin_urls):
        related_annotations_json_fp = os.path.join(related_annotations_dir, "%d.json" % i)
        related_htmls_database_dir = os.path.join(related_pages_dir, "%d.ldb" % i)
        related_full_annotations_json_fp = os.path.join(related_full_annotations_dir, "%d.json" % i)
        logging.info("Loading related annotation from from (%d): %s" % (i, related_annotations_json_fp))
        with open(related_annotations_json_fp, "rb") as i_fl:
            annotations = json.load(i_fl)
            related_htmls_ldb = husky.db.open(related_htmls_database_dir)
            with open(related_full_annotations_json_fp, "wb") as o_fl:
                for annotation in annotations["relatedArticlesAnnotations"]:
                    items = annotation["relatedItems"]
                    for j, item in enumerate(items):
                        logging.info("Processing %d of %d item." % (j+1, len(items)))
                        url = item["url"].encode("utf-8")

                        if url in annotations_cache:
                            item_annotation = annotations_cache[url]
                        else:
                            html = related_htmls_ldb.get(url)
                            if args.use_compression == 1:
                                try:
                                    html = lz4.decompress(html)
                                except Exception:
                                    continue
                            try:
                                item_annotation = annotator.annotate((url, html))
                                annotations_cache[url] = item_annotation
                            except Exception:
                                import traceback
                                traceback.print_exc()
                                item_annotation = None

                        if item_annotation is not None:
                            item["title"] += item_annotation.title
                            item["authors"] += item_annotation.authors
                            item["source"] += item_annotation.sources
                            item["dates"] += item_annotation.dates
                            item["images"] += item_annotation.images


                json.dump(annotations, o_fl, indent=4, sort_keys=False)
            related_htmls_ldb.close()


def step_9_normalize_data(args):
    """Extract full annotations from related pages HTML.
    """
    origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
    related_full_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR) #TODO
    normalized_annotations_dir = os.path.join(args.work_dir, NORMALIZED_ANNOTATIONS_DIR)
    if os.path.exists(normalized_annotations_dir):
        logging.info("Cleaning previous set_classified_data annotations directory %s" % normalized_annotations_dir)
        rm_cmd = "rm -rf %s" % normalized_annotations_dir
        os.system(rm_cmd)
    logging.info("Creating set_classified_data annotations directory: %s" % normalized_annotations_dir)
    os.mkdir(normalized_annotations_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    normalizer = husky.norm.pattern.ArticleNormalizer()
    dates = {}
    authors = {}
    normalized_titles_fp = os.path.join(normalized_annotations_dir, "titles.csv")
    normalized_authors_fp = os.path.join(normalized_annotations_dir, "authors.csv")
    normalized_sources_fp = os.path.join(normalized_annotations_dir, "sources.csv")
    normalized_dates_fp = os.path.join(normalized_annotations_dir, "dates.csv")
    with open(normalized_titles_fp, "wb") as titles_fl, \
         open(normalized_authors_fp, "wb") as authors_fl, \
         open(normalized_sources_fp, "wb") as sources_fl, \
         open(normalized_dates_fp, "wb") as dates_fl:
        for i, url in enumerate(origin_urls):
            related_full_annotations_json_fp = os.path.join(related_full_annotations_dir, "%d.json" % i)
            normalized_annotations_json_fp = os.path.join(normalized_annotations_dir, "%d.json" % i)

            with open(related_full_annotations_json_fp, "rb") as full_annotations_fl, \
                 open(normalized_annotations_json_fp, "wb") as normalized_annotations_fl:
                annotations = json.load(full_annotations_fl)

                for annotation in annotations["relatedArticlesAnnotations"]:
                    items = annotation["relatedItems"]

                    for j, item in enumerate(items):

                        for date in item["dates"]:
                            dates[date] = normalizer.classify_author_string(date)
                        for author in item["authors"]:
                            authors[author] = normalizer.normalize_author(author)

                        item["dates"] = normalizer.normalize(item["dates"])
                        item["authors"] = normalizer.normalize_authors(item["authors"])

        for date, norm_date in sorted(dates.items(), key=lambda x: x[1]):
            dates_fl.write("%s\t%s\n" % (date.encode("utf-8"), norm_date.encode("utf-8")))
        for author, norm_author in sorted(authors.items(), key=lambda x: x[1]):
            authors_fl.write("%s\t\t\t%r\n" % (author.encode("utf-8"), ""))


def step_10_evalualte_ner(args):

    related_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)
    origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
    input_documents_dir = os.path.join(args.work_dir, RELATED_FULL_DATA_DIR)
    html_db = husky.db.open(input_documents_dir).prefixed_db("html+")
    search_annotations = {}
    site_blacklist = husky.dicts.Blacklist.load(husky.dicts.Blacklist.BLACK_DOM)

    fetcher = husky.fetchers.PageFetcher()
    extractor = EntityExtractor()
    normalizer = EntityNormalizer()

    output_eval_dates_fl = os.path.join(args.eval_extr, "eval.date.csv")
    output_eval_authors_fl = os.path.join(args.eval_extr, "eval.author.csv")

    # Collect Search annotations.
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
    for i, url in enumerate(origin_urls):
        related_annotations_json_fp = os.path.join(related_annotations_dir, "%d.json" % i)
        with open(related_annotations_json_fp, "rb") as i_fl:
            annotations = json.load(i_fl)
            for related_item in annotations:
                url = related_item["url"].encode("utf-8")
                search_annotations[url] = related_item

    eval_entries = []
    with open(args.gold_extr, "rb") as i_gold:
        csv_reader = csv.reader(i_gold, delimiter=",", quotechar="\"")
        next(csv_reader, None)

        for url, true_authors, true_dates in csv_reader:

            true_authors = set() if true_authors == "<NONE>" else set(true_authors.lower().strip().split(" and "))
            true_dates = set() if true_dates == "<NONE>" else set(true_dates.lower().strip().split(" and "))

            pred_authors, pred_dates = None, None

            # Check if url is blacklisted
            if url in site_blacklist:
                pred_authors, pred_dates = [], []
                eval_entries.append((url, true_authors, true_dates, pred_authors, pred_dates))
                continue

            # Try to get HTML of url
            try:
                html = html_db.get(url)
                html = lz4.decompress(html) if args.use_compression == 1 else html
            except TypeError:
                logging.warning("HTML is not found. Skip %r." % url)
                try:
                    html = fetcher.fetch(url)
                except Exception:
                    logging.warning("HTML is not downloaded. Skip %r." % url)
                    html = "<html></html>"

            # Try to parse article
            try:
                article = extractor.parse_article(url, html)
            except Exception:
                logging.warning("HTML cannot be parsed. Skip %r." % url)
                pred_authors, pred_dates = [], []
                eval_entries.append((url, true_authors, true_dates, pred_authors, pred_dates))
                continue

            # Try find annotation
            try:
                annotation = search_annotations[url]
            except Exception:
                logging.warning("Annotation is not found. %r" % url)
                annotation = None
                pred_dates = []

            if pred_dates is None:
                try:
                    raw_dates = annotation["dates"]
                    pred_dates = normalizer.normalize_dates(raw_dates)
                    if len(pred_dates) > 1:
                        pred_dates = [min(pred_dates)]
                    pred_dates = set((d.lower() for d in pred_dates))
                except Exception:
                    logging.warning("Error when extracting dates. %r" % url)
                    pred_dates = set()

            if pred_authors is None:
                try:
                    raw_authors = extractor.extract_authors(article, annotation)
                    pred_authors = normalizer.normalize_authors(raw_authors, article=article)
                    pred_authors = set((a.name.lower() for a in pred_authors))
                except Exception:
                    logging.warning("Error when extracting authors. %r" % url)
                    pred_authors = set()

            eval_entries.append((url, true_authors, true_dates, pred_authors, pred_dates))

    authors_arp, authors_errors = husky.evaluation.compute_arp(((e[1], e[3]) for e in eval_entries))
    dates_arp, dates_errors = husky.evaluation.compute_arp(((e[2], e[4]) for e in eval_entries))

    # Write dates eval file.
    out_entries = [(e[0], e[2], e[4], err) for e, err in zip(eval_entries, dates_errors)]
    out_entries.sort(key=lambda row: row[-1])
    out_sorted = []
    for url, true_val, pred_val, errors in out_entries:
        true_val = "<NONE>" if len(true_val) == 0 else " AND ".join(sorted(true_val))
        pred_val = "<NONE>" if len(pred_val) == 0 else " AND ".join(sorted(pred_val))
        out_sorted.append((url, true_val, pred_val, errors))
    out_sorted = [("Url (P=%4f; R=%.4f; A=%.4f)." % dates_arp, "True Value", "Extr. Value", "Errors")] + out_sorted
    with open(output_eval_dates_fl, "wb") as fl:
        csv_writer = csv.writer(fl, delimiter=",", quotechar="\"")
        csv_writer.writerows(out_sorted)

    # Write authors eval file.
    out_entries = [(e[0], e[1], e[3], err) for e, err in zip(eval_entries, authors_errors)]
    out_entries.sort(key=lambda row: row[-1])
    out_sorted = []
    for url, true_val, pred_val, errors in out_entries:
        true_val = "<NONE>" if len(true_val) == 0 else " AND ".join(sorted(true_val))
        pred_val = "<NONE>" if len(pred_val) == 0 else " AND ".join(sorted(pred_val))
        out_sorted.append((url, true_val, pred_val, errors))
    out_sorted = [("Url (P=%4f; R=%.4f; A=%.4f)." % authors_arp, "True Value", "Extr. Value", "Errors")] + out_sorted
    with open(output_eval_authors_fl, "wb") as fl:
        csv_writer = csv.writer(fl, delimiter=",", quotechar="\"")
        csv_writer.writerows(out_sorted)


def step_11_gen_cr_data(args):

    related_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)
    origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
    input_documents_dir = os.path.join(args.work_dir, RELATED_FULL_DATA_DIR)
    output_documents_dir = os.path.join(args.work_dir, CROSS_REF_DIR)
    html_db = husky.db.open(input_documents_dir).prefixed_db("html+")
    site_blacklist = husky.dicts.Blacklist.load(husky.dicts.Blacklist.BLACK_DOM)

    fetcher = PageFetcher()
    text_util = TextUtil()
    extractor = EntityExtractor()
    normalizer = EntityNormalizer()

    clean_directory(output_documents_dir)

    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")

    # Extract data for cress-reference detection.
    # Data to extract:
    #   0. url
    #   1. html?
    #   2. text
    #   3. title
    #   4. sources
    #   5. pub date
    #   6. authors
    for i, origin_url in enumerate(origin_urls):


        # File with related annotations for given origin.
        rel_data_file = os.path.join(related_annotations_dir, "%d.json" % i)
        annotation_id = 1
        output_data = []
        with open(rel_data_file, "rb") as i_fl:

            for annotation in json.load(i_fl):

                url = annotation["url"].encode("utf-8")
                html = None
                title = None
                text = None
                sources = None
                pub_date = None
                authors = None

                # Check if url is Blacklisted
                if url in site_blacklist:
                    continue

                # 1. Get html from local database or Web.
                try:
                    html = html_db.get(url)
                    html = lz4.decompress(html) if args.use_compression == 1 else html
                except TypeError:
                    logging.warning("HTML is not found. Skip %r." % url)
                    try:
                        html = fetcher.fetch(url)
                    except Exception:
                        logging.warning("HTML is not downloaded. Skip %r." % url)
                        continue

                # Parse article.
                try:
                    article = extractor.parse_article(url, html)
                except Exception:
                    logging.warning("HTML cannot be parsed. Skip %r." % url)
                    continue

                # 2. Get text
                text = article.text

                # 3. Extract title
                titles = extractor.extract_titles(article)
                if len(titles) == 0:
                    logging.warning("Strange document. Skip")
                    continue
                else:
                    title = list(titles)[0]

                # 4. Extract sources
                sources = annotation["source"]

                # 5. Extract publication dates
                try:
                    raw_dates = annotation["dates"]
                    dates = normalizer.normalize_dates(raw_dates)
                    if len(dates) > 0:
                        pub_date = min(dates)
                    else:
                        pub_date = None
                except Exception:
                    logging.warning("Error when extracting dates. %r" % url)
                    pub_date = None

                # 6. Extract authors
                try:
                    raw_authors = extractor.extract_authors(article, annotation)
                    authors = normalizer.normalize_authors(raw_authors, article=article)
                    authors = list(set((a.name.lower() for a in authors)))
                except Exception:
                    logging.warning("Error when extracting authors. %r" % url)
                    authors = []

                rel_id = annotation_id
                annotation_id += 1

                output_data.append({

                    "id": rel_id,
                    "url": url,
                    "text": text,
                    "title": title,
                    "sources": sources,
                    "pub_date": pub_date,
                    "authors": authors,
                })

        with open(os.path.join(output_documents_dir, "%d.json" % i), "wb") as o_fl:

            json.dump(output_data, o_fl, indent=4)


def step_12_find_cross_references(args):
    """
    """

    origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
    input_documents_dir = os.path.join(args.work_dir, CROSS_REF_DIR)
    output_documents_dir = os.path.join(args.work_dir, CROSS_REF_OUT_DIR)

    clean_directory(output_documents_dir)

    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")

    for i, origin_url in enumerate(origin_urls):

        articles_fl = os.path.join(input_documents_dir, "%d.json" % i)
        with open(articles_fl, "rb") as i_fl:
            articles = json.load(i_fl)

        def read_ref_entry(article_data):
            date_str = article_data.get("pub_date")
            return ReferenceEntry(
                ref_id=article_data.get("id"),
                url=article_data.get("url"),
                html=article_data.get("html"),
                text=article_data.get("text"),
                title=article_data.get("title"),
                sources=article_data.get("sources"),
                pub_date=datetime.datetime.strptime(date_str, "%Y.%m.%d") if date_str else None,
                authors=article_data.get("authors"),
            )

        ref_index = ReferenceIndex((read_ref_entry(article) for article in articles))

        ref_index.print_titles()
        ref_index.index()

        print i, ref_index

        ref_index.find_cross_references(sent_window_size=3)

        if i > 0:
            break







STEPS = (
    (step_1_init_work_dir, "Prepare data for processing."),
    (step_2_fetch_origin_articles, "Fetch origin articles."),
    (step_3_extracting_article_sentences, "Extract origin bodies."),
    (step_4_extract_sentences, "Extract sentences/segments."),
    (step_5_request_gse, "Filter out non-important sentences and find related pages."),
    (step_6_extract_search_annotations, "Extract Google searcher annotations."),
    (step_7_fetch_related_pages, "Fetch related pages."),
    (step_8_extract_full_annotations, "Extract full annotations from related pages HTML."),
    (step_9_normalize_data, "Normalize data."),
    (step_10_evalualte_ner, "Evaluate named entity recognition."),
    (step_11_gen_cr_data, "Generate data for cross-reference detection."),
    (step_12_find_cross_references, "Find references between related articles.",)
)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("-v",
                           "--verbosity-level",
                           type=int,
                           default=1,
                           choices=(0, 1, 2))

    argparser.add_argument("--work-dir",
                           type=str,
                           help="Directory for storing temporary data for processing.",
                           default=None)

    argparser.add_argument("--origins-file-path",
                           type=str,
                           help="File with URLS used as origin links for mining stories.",
                           default=None)

    argparser.add_argument("--app-root",
                           type=str,
                           help="Directory containing processing package (e.g. `fenrir`).",
                           default=None)

    argparser.add_argument("--nlcd-conf-file",
                           type=str,
                           help="NLCD JSON configuration file containing API credentials and other information.",
                           default=None)

    argparser.add_argument("--pipeline-root",
                           type=str,
                           help="Directory containing pipeline python scripts.",
                           default=None)

    argparser.add_argument("--first-step",
                           type=int,
                           help="First step of processing (all previous steps will be skipped).",
                           default=1)

    argparser.add_argument("--last-step",
                           type=int,
                           help="Last step of processing (all following steps will be ignored).",
                           default=10)

    argparser.add_argument("--n-cpus",
                           type=int,
                           help="Maximum number of CPUs used for computation tasks.",
                           default=1)

    argparser.add_argument("--max-threads",
                           type=int,
                           help="Maximum number of threads used for streaming tasks (for example, downloading).",
                           default=10)

    argparser.add_argument("--use-compression",
                           type=int,
                           help="Pipeline will use lz4 to compress high volume temporary data (e.g. html of pages).",
                           default=0)

    argparser.add_argument("--gold-dates-norm",
                           type=str,
                           help="Path to the gold standard file for dates normalization.",
                           default=None)

    argparser.add_argument("--eval-dates-norm",
                           type=str,
                           help="Path to the evaluation results for dates normalization.",
                           default=None)

    argparser.add_argument("--gold-authors-norm",
                           type=str,
                           help="Path to the gold standard file for authors normalization.",
                           default=None)

    argparser.add_argument("--eval-authors-norm",
                           type=str,
                           help="Path to the evaluation results for authors normalization.",
                           default=None)

    argparser.add_argument("--gold-extr",
                           type=str,
                           help="Path to the gold standard file for extraction.",
                           default=None)

    argparser.add_argument("--eval-extr",
                           type=str,
                           help="Path to the evaluation results of extraction.",
                           default=None)

    argparser.add_argument("--gse-bottom-threshold",
                           type=int,
                           default=None)

    argparser.add_argument("--gse-upper-threshold",
                           type=int,
                           default=None)

    argparser.add_argument("--gse-query-size-heuristic",
                           type=int,
                           default=None)

    argparser.add_argument("--list-steps",
                           type=str,
                           help="Lists available steps.",
                           default=None)

    args = argparser.parse_args()

    if args.verbosity_level == 0:
        logging.basicConfig(level=logging.NOTSET)
    if args.verbosity_level == 1:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.verbosity_level == 2:
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    if args.list_steps is not None:
        sys.stdout.write("\nAvailable pipeline steps:\n")
        for i, (_, step_description) in enumerate(STEPS):
            sys.stdout.write("\t (%d) %s\n" % (i + 1, step_description))
        sys.stdout.write("\n\n")

    logging.info("\nRunning demo pipeline with the following options %r" % args)

    sys.path.append(args.app_root)

    sys.stderr.write("\nThe following steps (*) will be executed:\n\n")
    for i, (_, step_description) in enumerate(STEPS):
        step_i = i + 1
        if args.first_step <= step_i <= args.last_step:
            active_step = "*"
        else:
            active_step = " "
        sys.stderr.write("\t %s (%d) %s\n" % (active_step, step_i, step_description))
    sys.stderr.write("\n\n")

    for i, (step_function, step_description) in enumerate(STEPS):
        step_i = i + 1
        if args.first_step <= step_i <= args.last_step:
            logging.info("Starting step #%d: '%s'" % (step_i, step_description))
            step_function(args)
            logging.info("\n")
