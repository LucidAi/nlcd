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

import husky
import husky.db
import husky.dicts
import husky.evaluation
import husky.fetchers
import husky.extraction
import husky.api.google

from husky.extraction import Entity
from husky.extraction import TextMiner
from husky.extraction import EntityExtractor
from husky.extraction import EntityNormalizer

ORIGINS_FILE                    = "1.origins.text"
ORIGINS_HTML_DIR                = "2.origins.html"
ORIGINS_TEXT_DIR                = "3.origins.text"
ORIGINS_SENTENCES_DIR           = "4.origins.sents"
ORIGINS_FILTERED_DIR            = "5.origins.fsent"
RELATED_GSE_ANNOTATIONS_DIR     = "6.related.gse"
RELATED_FULL_DATA_DIR           = "7.related.data"
RELATED_FULL_ANNOTATIONS_DIR    = "8.related.annot"
NORMALIZED_ANNOTATIONS_DIR      = "9.norm.annot"
EVALUATION_DATA_DIR             = "10.evaluation.data"
EVALUATION_DIR                  = "11.evaluation"
GENDATE_DIR                     = "12.generated.data"


def clean_dir(path):
    if os.path.exists(path):
        os.system("rm -rf %s" % path)
    os.mkdir(path)


def step_1_preprocessing(args):
    """Creates work directory if not exists and copy origins file there.
    """
    if not os.path.exists(args.work_dir):
        logging.info("Creating work directory: %s" % args.work_dir)
        os.mkdir(args.work_dir)
    else:
        logging.info("Work directory already exists: %s" % args.work_dir)
    logging.info("Creating work directory: %s" % args.work_dir)
    cp_cmd = "cp -f %s %s" % (args.origins_file_path, os.path.join(args.work_dir, ORIGINS_FILE))
    logging.info("Calling command: %s" % cp_cmd)
    os.system(cp_cmd)
    return 0


def step_2_fetch_origin_articles(args):
    """Fetches origin articles HTML and saves them in work directory.
    """
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    articles_html_dir = os.path.join(args.work_dir, ORIGINS_HTML_DIR)
    if os.path.exists(articles_html_dir):
        logging.info("Cleaning previous articles directory %s" % articles_html_dir)
        rm_cmd = "rm -rf %s" % articles_html_dir
        os.system(rm_cmd)
    logging.info("Creating articles html directory: %s" % articles_html_dir)
    os.mkdir(articles_html_dir)
    fetcher = husky.fetchers.PageFetcher()
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    logging.info("Fetching origins to using %s threads: %s" % (args.max_threads, articles_html_dir))
    async_articles_list = fetcher.fetch_documents(origin_urls, max_threads=args.max_threads)
    def save_html(j_response):
        j, response = j_response
        file_name = os.path.join(articles_html_dir, "%d.html" % j)
        with open(file_name, "wb") as fl:
            fl.write(fetcher.response_to_utf_8(response))
    map(save_html, enumerate(async_articles_list))
    return 0


def step_3_extracting_article_sentences(args):
    """Reads origin articles from work directory and extract clean text from them.
    """
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    articles_html_dir = os.path.join(args.work_dir, ORIGINS_HTML_DIR)
    articles_text_dir = os.path.join(args.work_dir, ORIGINS_TEXT_DIR)
    if os.path.exists(articles_text_dir):
        logging.info("Cleaning previous articles texts directory %s" % articles_text_dir)
        rm_cmd = "rm -rf %s" % articles_text_dir
        os.system(rm_cmd)
    logging.info("Creating articles text directory: %s" % articles_text_dir)
    os.mkdir(articles_text_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    logging.info("Extracting articles texts to: %s" % articles_text_dir)
    text_miner = TextMiner()
    for i, url in enumerate(origin_urls):
        logging.info("Extracting text from (%d): %s" % (i, url))
        html_file_name = os.path.join(articles_html_dir, "%d.html" % i)
        text_file_name = os.path.join(articles_text_dir, "%d.json" % i)
        with open(html_file_name, "rb") as i_fl:
            html = i_fl.read()
            article = text_miner.extract_article(url, html)
            with open(text_file_name, "wb") as o_fl:
                json.dump({
                    "url":      article.url,
                    "title":    article.title.encode("utf-8"),
                    "text":     article.text.encode("utf-8"),
                    "lang_id":  article.lang_id,
                }, o_fl, indent=4, ensure_ascii=False)


def step_4_extract_sentences(args):
    """Extract sentences and segment them.
    """
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    articles_text_dir = os.path.join(args.work_dir, ORIGINS_TEXT_DIR)
    articles_sentences_dir = os.path.join(args.work_dir, ORIGINS_SENTENCES_DIR)
    if os.path.exists(articles_sentences_dir):
        logging.info("Cleaning previous articles (raw) directory %s" % articles_sentences_dir)
        rm_cmd = "rm -rf %s" % articles_sentences_dir
        os.system(rm_cmd)
    logging.info("Creating articles text directory: %s" % articles_text_dir)
    os.mkdir(articles_sentences_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    logging.info("Sentences, saving to: %s" % articles_sentences_dir)
    for i, url in enumerate(origin_urls):
        logging.info("Loading article text from (%d): %s" % (i, url))
        text_json_file_name = os.path.join(articles_text_dir, "%d.json" % i)
        sentences_json_name = os.path.join(articles_sentences_dir, "%d.json" % i)
        text_miner = TextMiner()
        with open(text_json_file_name, "rb") as i_fl:
            article = json.load(i_fl)
            with open(sentences_json_name, "wb") as o_fl:
                url = article["url"].encode("utf-8")
                title = article["title"].encode("utf-8")
                text = article["text"].encode("utf-8")
                lang_id = article["lang_id"].encode("utf-8")
                sentences = text_miner.sent_tokenize(text)
                quoted = text_miner.extract_quoted(text)
                all_sentence = text_miner.combine_sentences(sentences, quoted)
                json.dump({
                    "url": url,
                    "title": title,
                    "text": text,
                    "lang_id": lang_id,
                    "sentences": all_sentence,
                    "quoted": quoted,
                }, o_fl, indent=4)


def step_5_filter_sentences(args):
    """Filter out non-important sentences and find related pages.
    """
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    articles_sentences_dir = os.path.join(args.work_dir, ORIGINS_SENTENCES_DIR)
    articles_filtered_dir = os.path.join(args.work_dir, ORIGINS_FILTERED_DIR)
    with open(args.nlcd_conf_file, "rb") as fl:
        nlcd_config = json.load(fl)
    if os.path.exists(articles_filtered_dir):
        logging.info("Cleaning previous sentences (filtered) directory %s" % articles_filtered_dir)
        rm_cmd = "rm -rf %s" % articles_filtered_dir
        os.system(rm_cmd)
    logging.info("Creating directory for storing filtered sentences: %s" % articles_filtered_dir)
    os.mkdir(articles_filtered_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    logging.info("Filtered sentences, saving to: %s" % articles_filtered_dir)
    search_api = husky.api.create_api(nlcd_config["nlcd"]["searchApi"])
    logging.info("Created sentence filterer %r" % search_api)
    for i, url in enumerate(origin_urls):
        logging.info("Loading article sentences from (%d): %s" % (i, url))
        sentences_json_file_name = os.path.join(articles_sentences_dir, "%d.json" % i)
        sentences_json_name = os.path.join(articles_filtered_dir, "%d.json" % i)
        with open(sentences_json_file_name, "rb") as i_fl:
            article = json.load(i_fl)
            with open(sentences_json_name, "wb") as o_fl:
                url = article["url"].encode("utf-8")
                title = article["title"].encode("utf-8")
                text = article["text"].encode("utf-8")
                lang_id = article["lang_id"].encode("utf-8")
                sentences = [s.encode("utf-8") for s in article["sentences"]]
                logging.info("Start filtering sentences (%d)." % len(sentences))
                filtered_sentences = search_api.filter_sentences(sentences)
                filtered_sentences = list(filtered_sentences)
                json.dump({
                    "url": url,
                    "title": title,
                    "text": text,
                    "lang_id": lang_id,
                    "sentences": sentences,
                    "filteredSentences": filtered_sentences,
                }, o_fl, indent=4)


def step_6_extract_search_annotations(args):
    """Extract Google searcher annotations.
    """
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    articles_filtered_dir = os.path.join(args.work_dir, ORIGINS_FILTERED_DIR)
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
        filtered_sentences_json_file_name = os.path.join(articles_filtered_dir, "%d.json" % i)
        related_annotations_json_file_name = os.path.join(related_annotations_dir, "%d.json" % i)
        with open(filtered_sentences_json_file_name, "rb") as i_fl:
            article = json.load(i_fl)
            with open(related_annotations_json_file_name, "wb") as o_fl:
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
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
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
        related_annotations_json_file_name = os.path.join(related_annotations_dir, "%d.json" % i)
        logging.info("Loading related annotation from from (%d): %s" % (i, related_annotations_json_file_name))
        with open(related_annotations_json_file_name, "rb") as i_fl:
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
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
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
        related_annotations_json_file_name = os.path.join(related_annotations_dir, "%d.json" % i)
        related_htmls_database_dir = os.path.join(related_pages_dir, "%d.ldb" % i)
        related_full_annotations_json_file_name = os.path.join(related_full_annotations_dir, "%d.json" % i)
        logging.info("Loading related annotation from from (%d): %s" % (i, related_annotations_json_file_name))
        with open(related_annotations_json_file_name, "rb") as i_fl:
            annotations = json.load(i_fl)
            related_htmls_ldb = husky.db.open(related_htmls_database_dir)
            with open(related_full_annotations_json_file_name, "wb") as o_fl:
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
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
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
    normalized_titles_file_name = os.path.join(normalized_annotations_dir, "titles.csv")
    normalized_authors_file_name = os.path.join(normalized_annotations_dir, "authors.csv")
    normalized_sources_file_name = os.path.join(normalized_annotations_dir, "sources.csv")
    normalized_dates_file_name = os.path.join(normalized_annotations_dir, "dates.csv")
    with open(normalized_titles_file_name, "wb") as titles_fl, \
         open(normalized_authors_file_name, "wb") as authors_fl, \
         open(normalized_sources_file_name, "wb") as sources_fl, \
         open(normalized_dates_file_name, "wb") as dates_fl:
        for i, url in enumerate(origin_urls):
            related_full_annotations_json_file_name = os.path.join(related_full_annotations_dir, "%d.json" % i)
            normalized_annotations_json_file_name = os.path.join(normalized_annotations_dir, "%d.json" % i)

            with open(related_full_annotations_json_file_name, "rb") as full_annotations_fl, \
                 open(normalized_annotations_json_file_name, "wb") as normalized_annotations_fl:
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


def step_10_evaluation(args):

    related_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    input_documents_dir = os.path.join(args.work_dir, RELATED_FULL_DATA_DIR)
    html_db = husky.db.open(input_documents_dir).prefixed_db("html+")
    search_annotations = {}
    site_blacklist = husky.dicts.WordList.load(husky.dicts.WordList.BLACK_DOM)

    fetcher = husky.fetchers.PageFetcher()
    extractor = EntityExtractor()
    normalizer = EntityNormalizer()

    output_eval_dates_fl = os.path.join(args.eval_extr, "eval.date.csv")
    output_eval_authors_fl = os.path.join(args.eval_extr, "eval.author.csv")


    # Collect Search annotations.
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
    for i, url in enumerate(origin_urls):
        related_annotations_json_file_name = os.path.join(related_annotations_dir, "%d.json" % i)
        with open(related_annotations_json_file_name, "rb") as i_fl:
            annotations = json.load(i_fl)
            for related_item in annotations:
                url = related_item["url"].encode("utf-8")
                search_annotations[url] = related_item

    i = 0
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


def step_11_gen_test_data(args):

    related_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    input_documents_dir = os.path.join(args.work_dir, RELATED_FULL_DATA_DIR)
    generated_data_dir = os.path.join(args.work_dir, EVALUATION_DATA_DIR)
    generated_data_file = os.path.join(generated_data_dir, "generated.csv")
    input_db = husky.db.open(input_documents_dir)
    input_html_db = input_db.prefixed_db("html+")
    output_rows = []
    search_annotations = {}
    site_blacklist = husky.dicts.WordList.load(husky.dicts.WordList.BLACK_DOM)

    extractor = EntityExtractor()
    normalizer = EntityNormalizer()

    # Collect urls, already used in gold data.
    eval_urls = set()
    with open(args.gold_extr, "rb") as i_gold:
        csv_reader = csv.reader(i_gold, delimiter=",", quotechar="\"")
        next(csv_reader, None)
        for row in csv_reader:
            eval_urls.add(row[0])

    # Collect Search annotations.
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
    for i, url in enumerate(origin_urls):
        related_annotations_json_file_name = os.path.join(related_annotations_dir, "%d.json" % i)
        with open(related_annotations_json_file_name, "rb") as i_fl:
            annotations = json.load(i_fl)
            for related_item in annotations:
                url = related_item["url"].encode("utf-8")
                search_annotations[url] = related_item

    # Extract authors and dates
    for url, html in input_html_db:
        if url in site_blacklist or url in eval_urls:
            continue
        try:
            html = lz4.decompress(html) if args.use_compression == 1 else html
        except ValueError:
            continue

        # Extract Dates
        try:
            search_item = search_annotations[url]
            dates_raw = search_item["dates"]
            dates_norm = normalizer.normalize_dates(dates_raw)
            dates = "<NONE>" if len(dates_norm) == 0 else " AND ".join(dates_norm)
        except Exception:
            dates = "ERROR_OCCURRED"

        # Extract Authors
        try:
            article = extractor.parse_article(url, html)
            entities_raw = extractor.extract_authors(article)
            entities_norm = normalizer.normalize_authors(entities_raw, article=article)
            authors = set([e.name for e in entities_norm if e.ent_rel == Entity.REL.AUTHOR])
            authors = "<NONE>" if len(authors) == 0 else " AND ".join(authors)
        except Exception:
            authors = "ERROR_OCCURRED"

        output_rows.append((url, authors, dates))

    # Sort by url
    output_rows.sort(key=lambda row: row[0])
    output_rows = [(str(i), r[0], r[1], r[2]) for i, r in enumerate(output_rows)]
    output_rows = [("#", "Url", "Authors", "Dates")] + output_rows
    with open(generated_data_file, "wb") as fl:
        csv_writer = csv.writer(fl, delimiter=",", quotechar="\"")
        csv_writer.writerows(output_rows)



STEPS = (
    (step_1_preprocessing, "Prepare data for processing."),
    (step_2_fetch_origin_articles, "Fetch origin articles."),
    (step_3_extracting_article_sentences, "Extract origin sentences."),
    (step_4_extract_sentences, "Extract sentences/segments."),
    (step_5_filter_sentences, "Filter out non-important sentences and find related pages."),
    (step_6_extract_search_annotations, "Extract Google searcher annotations."),
    (step_7_fetch_related_pages, "Fetch related pages."),
    (step_8_extract_full_annotations, "Extract full annotations from related pages HTML."),
    (step_9_normalize_data, "Normalize data."),
    (step_10_evaluation, "Compute accuracy and coverage of extraction methods."),
    (step_11_gen_test_data, "Generate test data.")
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
