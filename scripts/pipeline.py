#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import os
import sys
import glob
import json
import logging
import argparse
import itertools

import fenrir
import fenrir.fetcher
import fenrir.extraction
import fenrir.extraction.base
import fenrir.extraction.entity
import fenrir.api.google


ORIGINS_FILE            = "1.origins.txt"
ORIGINS_HTML_DIR        = "2.orignins.html"
ORIGINS_TEXT_DIR        = "3.orignins.text"
ORIGINS_FILTERED_DIR    = "4.filtered.text"


def step_1_preprocessing(args):
    """Creates work directory if not exists and copy origins file there.
    """
    if not os.path.exists(args.work_dir):
        logging.info("Creating work directory: %s" % args.work_dir)
        os.mkdir(args.workdir)
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
    fetcher = fenrir.fetcher.Fetcher()
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    logging.info("Fetching origins to using %s threads: %s" % (args.max_threads, articles_html_dir))
    async_articles_list = fetcher.fetch_documents(origin_urls, max_threads=args.max_threads)
    def save_html(i_response):
        i, response = i_response
        file_name = os.path.join(articles_html_dir, "%d.html" % i)
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
    text_preproc = fenrir.extraction.base.TextPreprocessor()
    for i, url in enumerate(origin_urls):
        logging.info("Extracting text from (%d): %s" % (i, url))
        html_file_name = os.path.join(articles_html_dir, "%d.html" % i)
        text_file_name = os.path.join(articles_text_dir, "%d.json" % i)
        with open(html_file_name, "rb") as i_fl:
            html = i_fl.read()
            article = text_preproc.extract_article(url, html)
            with open(text_file_name, "wb") as o_fl:
                json.dump({
                    "url": article.url,
                    "title": article.title.encode("utf-8"),
                    "text": article.text.encode("utf-8"),
                    "authors": [a.encode("utf-8") for a in article.authors],
                    "keywords": [kw.encode("utf-8") for kw in article.keywords],
                    "summary": article.summary.encode("utf-8"),
                    "langid": text_preproc.langid(article.text),
                }, o_fl, indent=4, ensure_ascii=False)


def step_4_extract_key_sentences(args):
    origins_fl = os.path.join(args.work_dir, ORIGINS_FILE)
    articles_text_dir = os.path.join(args.work_dir, ORIGINS_TEXT_DIR)
    articles_filtered_dir = os.path.join(args.work_dir, ORIGINS_FILTERED_DIR)
    with open(args.nlcd_conf_file, "rb") as fl:
        nlcd_config = json.load(fl)
    if os.path.exists(articles_filtered_dir):
        logging.info("Cleaning previous articles (filtered) directory %s" % articles_filtered_dir)
        rm_cmd = "rm -rf %s" % articles_filtered_dir
        os.system(rm_cmd)
    logging.info("Creating articles text directory: %s" % articles_text_dir)
    os.mkdir(articles_filtered_dir)
    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")
        logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
    logging.info("Filtering sentences, saving to: %s" % articles_filtered_dir)
    cse_conf = nlcd_config["nlcd"]["searchApi"][0]
    cse_key = cse_conf["googleApiKey"]
    cse_engine = cse_conf["googleEngineId"]
    sentence_filterer = fenrir.api.google.CseAPI(cse_key, cse_engine)
    min_threshold, max_threshold = map(int, args.cse_thresholds.split(":"))
    logging.info("Created sentence filterer %r" % sentence_filterer)
    for i, url in enumerate(origin_urls):
        logging.info("Loading article text from (%d): %s" % (i, url))
        text_json_file_name = os.path.join(articles_text_dir, "%d.json" % i)
        filtered_json_name = os.path.join(articles_filtered_dir, "%d.json" % i)
        text_preproc = fenrir.extraction.base.TextPreprocessor()
        with open(text_json_file_name, "rb") as i_fl:
            article = json.load(i_fl)
            with open(filtered_json_name, "wb") as o_fl:



                url = article["url"].encode("utf-8")
                title = article["title"].encode("utf-8")
                text = article["text"].encode("utf-8")
                authors = [a.encode("utf-8") for a in article["authors"]],
                keywords = [kw.encode("utf-8") for kw in article["keywords"]]
                summary = article["summary"].encode("utf-8")
                langid = text_preproc.langid(article["text"])[0]


                sentenes = text_preproc.sent_segmentize(text)
                sentenes.extend(text_preproc.sent_segmentize(summary))
                quoted = text_preproc.extract_quoted(sentenes)
                all_sentences = list(set(sentenes+quoted))
                filtered_sentences = list(sentence_filterer.filter_sentences(all_sentences, min_threshold, max_threshold))
                json.dump({
                    "url": url,
                    "title": title,
                    "text": text,
                    "authors": authors,
                    "keywords": keywords,
                    "summary": summary,
                    "langid": langid,
                    "sentences": filtered_sentences,
                }, o_fl, indent=4, ensure_ascii=False)


STEPS = (

    (step_1_preprocessing, "Prepare data for processing."),
    (step_2_fetch_origin_articles, "Fetch origin articles."),
    (step_3_extracting_article_sentences, "Extract origin sentences."),
    (step_4_extract_key_sentences, "Filter non important sentences/segments."),

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

    argparser.add_argument("--cse-thresholds",
                           type=str,
                           help="Google CSE result number thresholds to recognize given query as 'important'.",
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
