#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import os
import lz4
import sys
import json
import plyvel
import logging
import argparse

import fenrir
import fenrir.fetcher
import fenrir.extraction
import fenrir.extraction.base
import fenrir.extraction.entity
import fenrir.extraction.google
import fenrir.api.google


ORIGINS_FILE                  = "1.origins.text"
ORIGINS_HTML_DIR              = "2.origins.html"
ORIGINS_TEXT_DIR              = "3.origins.text"
ORIGINS_SENTENCES_DIR         = "4.origins.sents"
ORIGINS_FILTERED_DIR          = "5.origins.fsent"
RELATED_ANNOTATIONS_DIR       = "6.related.annot"
RELATED_PAGES_DIR             = "7.related.html"
RELATED_FULL_ANNOTATIONS      = "8.related.full"


def MB(number):
    return 1024 * 1024 * number


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
    fetcher = fenrir.fetcher.PageFetcher()
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
    """Reads origin articles from work directory and extract clean text from them
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
    text_miner = fenrir.extraction.base.TextMiner()
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
    """"""
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
        text_miner = fenrir.extraction.base.TextMiner()
        with open(text_json_file_name, "rb") as i_fl:
            article = json.load(i_fl)
            with open(sentences_json_name, "wb") as o_fl:
                url = article["url"].encode("utf-8")
                title = article["title"].encode("utf-8")
                text = article["text"].encode("utf-8")
                lang_id = article["lang_id"].encode("utf-8")
                sentences = text_miner.sent_tokenize(text)
                quoted = text_miner.extract_quoted(sentences)
                sentences = list(set(sentences + quoted))
                json.dump({
                    "url": url,
                    "title": title,
                    "text": text,
                    "lang_id": lang_id,
                    "sentences": sentences,
                }, o_fl, indent=4)


def step_5_filter_sentences(args):
    """"""
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
    search_api = fenrir.api.create_api(nlcd_config["nlcd"]["searchApi"])
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
    """"""
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    articles_filtered_dir = os.path.join(args.work_dir, ORIGINS_FILTERED_DIR)
    related_annotations_dir = os.path.join(args.work_dir, RELATED_ANNOTATIONS_DIR)
    if os.path.exists(related_annotations_dir):
        logging.info("Cleaning previous related annotations directory %s" % related_annotations_dir)
        rm_cmd = "rm -rf %s" % related_annotations_dir
        os.system(rm_cmd)
    logging.info("Creating related annotations directory: %s" % related_annotations_dir)
    os.mkdir(related_annotations_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    annotations_extractor = fenrir.extraction.google.CseAnnotationExtractor()
    logging.info("Created annotations extractor: %r" % annotations_extractor)
    for i, url in enumerate(origin_urls):
        logging.info("Loading article sentences from (%d): %s" % (i, url))
        filtered_sentences_json_file_name = os.path.join(articles_filtered_dir, "%d.json" % i)
        related_annotations_json_file_name = os.path.join(related_annotations_dir, "%d.json" % i)
        with open(filtered_sentences_json_file_name, "rb") as i_fl:
            article = json.load(i_fl)
            with open(related_annotations_json_file_name, "wb") as o_fl:
                url = article["url"].encode("utf-8")
                title = article["title"].encode("utf-8")
                lang_id = article["lang_id"].encode("utf-8")
                filtered_sentences = article["filteredSentences"]
                annotations = []
                for sentence_entry in filtered_sentences:
                    sent_text = sentence_entry["text"]
                    sent_total_results = sentence_entry["totalResults"]
                    sent_api_response = sentence_entry["apiResponse"]
                    related_items = []
                    for related_item in sent_api_response["items"]:
                        annotation = annotations_extractor.annotate(related_item)
                        related_items.append({
                            "url": annotation.url,
                            "title": annotation.title,
                            "authors": annotation.authors,
                            "source": annotation.sources,
                            "dates": annotation.dates,
                            "images": annotation.images,
                        })
                    annotations.append({
                        "sentenceText": sent_text,
                        "sentenceFreq": sent_total_results,
                        "relatedItems": related_items,
                    })
                json.dump({
                    "originArticle": {
                        "url": url,
                        "title": title,
                        "lang_id": lang_id,
                    },
                    "relatedArticlesAnnotations": annotations,
                }, o_fl, indent=4, sort_keys=False)


def step_7_fetch_related_pages(args):
    """"""
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    related_annotations_dir = os.path.join(args.work_dir, RELATED_ANNOTATIONS_DIR)
    related_pages_dir = os.path.join(args.work_dir, RELATED_PAGES_DIR)
    if os.path.exists(related_annotations_dir):
        logging.info("Cleaning previous related pages directory %s" % related_pages_dir)
        rm_cmd = "rm -rf %s" % related_pages_dir
        os.system(rm_cmd)
    logging.info("Creating related pages directory: %s" % related_pages_dir)
    os.mkdir(related_pages_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    fetcher = fenrir.fetcher.PageFetcher()
    for i, url in enumerate(origin_urls):
        related_annotations_json_file_name = os.path.join(related_annotations_dir, "%d.json" % i)
        related_htmls_database_dir = os.path.join(related_pages_dir, "%d.ldb" % i)
        os.mkdir(related_htmls_database_dir)
        logging.info("Loading related annotation from from (%d): %s" % (i, related_annotations_json_file_name))
        with open(related_annotations_json_file_name, "rb") as i_fl:
            annotation = json.load(i_fl)
            related_annotations = annotation["relatedArticlesAnnotations"]
            related_htmls_ldb = plyvel.DB(related_htmls_database_dir,
                                          write_buffer_size=MB(1024),
                                          block_size=MB(512),
                                          bloom_filter_bits=8,
                                          create_if_missing=True,
                                          error_if_exists=True)
            urls = set()
            for annotation in related_annotations:
                for related_item in annotation["relatedItems"]:
                    urls.add(related_item["url"].encode("utf-8"))
            urls = list(urls)
            logging.info("Loaded %d urls from annotations, start fetching." % len(urls))
            async_related_list = fetcher.fetch_documents(urls, max_threads=args.max_threads)
            def save_html(j_response):
                j, response = j_response
                if j % 10 == 0 and j > 0:
                    logging.info("Added %d/%d." % (len(urls), j+1))
                html = fetcher.response_to_utf_8(response)
                if args.use_compression == 1:
                    html = lz4.compressHC(html)
                related_htmls_ldb.put(response.url.encode("utf-8"), html)
            map(save_html, enumerate(async_related_list))
            logging.info("Added %d/%d." % (len(urls), len(urls)))
            related_htmls_ldb.close()
        logging.info("Fetching completed.")


STEPS = (

    (step_1_preprocessing, "Prepare data for processing."),
    (step_2_fetch_origin_articles, "Fetch origin articles."),
    (step_3_extracting_article_sentences, "Extract origin sentences."),
    (step_4_extract_sentences, "Extract sentences/segments."),
    (step_5_filter_sentences, "Filter out non-important sentences."),
    (step_6_extract_search_annotations, "Extract searcher annotations."),
    (step_7_fetch_related_pages, "Fetch related pages.")
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

    argparser.add_argument("--list-steps",
                           type=str,
                           help="Lists available steps.",
                           default=None)

    args = argparser.parse_args()

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
