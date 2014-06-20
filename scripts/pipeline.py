#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import os
import csv
import lz4
import sys
import json
import plyvel
import logging
import argparse

import fenrir
import fenrir.util
import fenrir.fetcher
import fenrir.extraction
import fenrir.extraction.web
import fenrir.extraction.base
import fenrir.extraction.entity
import fenrir.extraction.google
import fenrir.api.google
import fenrir.normalization.pattern


ORIGINS_FILE                    = "1.origins.text"
ORIGINS_HTML_DIR                = "2.origins.html"
ORIGINS_TEXT_DIR                = "3.origins.text"
ORIGINS_SENTENCES_DIR           = "4.origins.sents"
ORIGINS_FILTERED_DIR            = "5.origins.fsent"
RELATED_ANNOTATIONS_DIR         = "6.related.annot"
RELATED_PAGES_DIR               = "7.related.html"
RELATED_FULL_ANNOTATIONS_DIR    = "8.related.full"
NORMALIZED_ANNOTATIONS_DIR      = "9.norm.annot"
COVERAGE_DIR                    = "10.coverage"


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
        text_miner = fenrir.extraction.base.TextMiner()
        with open(text_json_file_name, "rb") as i_fl:
            article = json.load(i_fl)
            with open(sentences_json_name, "wb") as o_fl:
                url = article["url"].encode("utf-8")
                title = article["title"].encode("utf-8")
                text = article["text"].encode("utf-8")
                lang_id = article["lang_id"].encode("utf-8")
                sentences = text_miner.sent_tokenize(text)
                quoted = text_miner.extract_quoted(text)
                sentences = [s for s in list(set(sentences + quoted)) if len(s) > 10]
                json.dump({
                    "url": url,
                    "title": title,
                    "text": text,
                    "lang_id": lang_id,
                    "sentences": sentences,
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
    """Extract Google searcher annotations.
    """
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
                    if sent_total_results == 0:
                        continue
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
    """Fetch related pages.
    """
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
            related_annotations = json.load(i_fl)["relatedArticlesAnnotations"]
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
                related_htmls_ldb.put(url, html)
            map(save_html, enumerate(async_related_list))
            logging.info("Added %d/%d." % (len(urls), len(urls)))
            related_htmls_ldb.close()
        logging.info("Fetching completed.")


def step_8_extract_full_annotations(args):
    """Extract full annotations from related pages HTML.
    """
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    related_annotations_dir = os.path.join(args.work_dir, RELATED_ANNOTATIONS_DIR)
    related_pages_dir = os.path.join(args.work_dir, RELATED_PAGES_DIR)
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
    annotator = fenrir.extraction.web.HtmlAnnotationsExtractor()
    annotations_cache = {}
    for i, url in enumerate(origin_urls):
        related_annotations_json_file_name = os.path.join(related_annotations_dir, "%d.json" % i)
        related_htmls_database_dir = os.path.join(related_pages_dir, "%d.ldb" % i)
        related_full_annotations_json_file_name = os.path.join(related_full_annotations_dir, "%d.json" % i)
        logging.info("Loading related annotation from from (%d): %s" % (i, related_annotations_json_file_name))
        with open(related_annotations_json_file_name, "rb") as i_fl:
            annotations = json.load(i_fl)
            related_htmls_ldb = plyvel.DB(related_htmls_database_dir, create_if_missing=False)
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
    related_full_annotations_dir = os.path.join(args.work_dir, RELATED_ANNOTATIONS_DIR) #TODO
    normalized_annotations_dir = os.path.join(args.work_dir, NORMALIZED_ANNOTATIONS_DIR)
    if os.path.exists(normalized_annotations_dir):
        logging.info("Cleaning previous normalized annotations directory %s" % normalized_annotations_dir)
        rm_cmd = "rm -rf %s" % normalized_annotations_dir
        os.system(rm_cmd)
    logging.info("Creating normalized annotations directory: %s" % normalized_annotations_dir)
    os.mkdir(normalized_annotations_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    normalizer = fenrir.normalization.pattern.PatterMatchNormalizer()

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
                            dates[date] = normalizer.normalize_date(date)
                        for author in item["authors"]:
                            authors[author] = normalizer.normalize_author(author)

                        item["dates"] = normalizer.normalize_dates(item["dates"])
                        item["authors"] = normalizer.normalize_authors(item["authors"])


        for date, norm_date in sorted(dates.items(), key=lambda x: x[1]):
            dates_fl.write("%s\t%s\n" % (date.encode("utf-8"), norm_date.encode("utf-8")))
        for author, norm_author in sorted(authors.items(), key=lambda x: x[1]):
            authors_fl.write("%s\t\t\t%r\n" % (author.encode("utf-8"), ""))

def step_10_compute_coverage(args):
    coverage_temp_dir = os.path.join(args.work_dir, COVERAGE_DIR)
    if os.path.exists(coverage_temp_dir):
        logging.info("Cleaning previous coverage temp directory %s" % coverage_temp_dir)
        rm_cmd = "rm -rf %s" % coverage_temp_dir
        os.system(rm_cmd)
    logging.info("Creating coverage temp directory: %s" % coverage_temp_dir)
    os.mkdir(coverage_temp_dir)
    normalizer = fenrir.normalization.pattern.PatterMatchNormalizer()
    # Compute dates extraction accuracy and coverage.
    output_values = []
    with open(args.gold_dates, "rb") as i_gold_dates:
        csv_reader = csv.reader(i_gold_dates, delimiter=",", quotechar="\"")
        next(csv_reader, None)
        for i, (input_str, true_value) in enumerate(csv_reader):
            pred_value = normalizer.normalize_date(input_str)
            output_row = (input_str, true_value, pred_value, int(true_value == pred_value))
            output_values.append(output_row)
        output_values.sort(key=lambda row: row[-1])
    apr = fenrir.util.evaluate_extraction(output_values)
    with open(args.eval_dates, "wb") as o_eval_dates:
        csv_writer = csv.writer(o_eval_dates, delimiter=",", quotechar="\"")
        header = ("a=%.4f;p=%.4f;r=%.4f Inp.String" % apr,
                  "True Value",
                  "Extracted Value",
                  "Is Correct")
        rows = [header] + output_values
        csv_writer.writerows(rows)


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
    (step_10_compute_coverage, "Compute accuracy and coverage of extraction methods."),
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

    argparser.add_argument("--gold-dates",
                           type=str,
                           help="Path to the gold standard file for dates extraction.",
                           default=0)

    argparser.add_argument("--eval-dates",
                           type=str,
                           help="Path to the evaluation results for dates extraction.",
                           default=0)

    argparser.add_argument("--gold-authors",
                           type=str,
                           help="Path to the gold standard file for authors extraction.",
                           default=0)

    argparser.add_argument("--eval-authors",
                           type=str,
                           help="Path to the evaluation results for authors extraction.",
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
