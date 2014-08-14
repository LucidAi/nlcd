#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import os
import sys
import csv
import json
import logging
import argparse

import husky.db
import husky.eval

from husky.fetchers import PageFetcher
from husky.extraction import EntityExtractor


DOCUMENTS_DB_PATH = "documents.ldb"


def clean_directory(path):
    """
    Create path if not exist otherwise recreates it.
    """
    if os.path.exists(path):
        os.system("rm -rf %s" % path)
    os.mkdir(path)


def step_1_init_work_dir(args):
    """
    Create work directory and download links.
    """
    clean_directory(args.work_dir)

    documents_db_path = os.path.join(args.work_dir, DOCUMENTS_DB_PATH)
    documents_db = husky.db.create(documents_db_path)

    fetcher = PageFetcher()

    with open(args.gold, "r") as i_gold:
        gold_entries = csv.reader(i_gold, delimiter=",", quotechar="\"")
        gold_entries.next()
        url2html_dict = {entry[0]: None for entry in gold_entries}

    logging.info("Fetching %d documents" % len(url2html_dict))
    fetcher.fetch_urls(url2html_dict, max_threads=args.max_threads)

    for url, html in url2html_dict.iteritems():
        documents_db.put(url, html)


def step_2_eval_titles(args):
    """Evaluate titles extraction."""

    o_eval_fp = os.path.join(args.work_dir, "eval_title.csv")
    documents_db_path = os.path.join(args.work_dir, DOCUMENTS_DB_PATH)
    documents_db = husky.db.open(documents_db_path)
    eval_data = []

    extractor = EntityExtractor()

    with open(args.cse, "rb") as cse_fl:
        cse = json.load(cse_fl)

    urls = set()

    with open(args.gold, "rb") as i_gold:

        gold_entries = csv.reader(i_gold, delimiter=",", quotechar="\"")
        gold_entries.next()
        gold_entries = list(gold_entries)

        for i, entry in enumerate(gold_entries):

            # if i > 5:
            #     break

            url = entry[0]
            urls.add(url)
            cse_entry = cse.get(url)

            if cse_entry is None:
                print url

            continue
            html = documents_db.get(url)
            article = extractor.parse_article(url, html)

            # Gold
            gold_title = entry[1]

            # NLCD
            nlcd_title = extractor.extract_titles(article, None, select_best=True)

            # Newspaper
            np_title = article.title

            # CSE
            cse_title = None

            eval_data.append((gold_title, nlcd_title, np_title, cse_title))

    print
    print
    for u in cse.iterkeys():
        if u not in urls:
            print u

    return
    gold_out, methods_out = husky.eval.compute_title_prf(eval_data)

    with open(o_eval_fp, "wb") as o_eval:

        eval_csv = csv.writer(o_eval, delimiter=",", quotechar="\"")

        eval_csv.writerow([
            "#",
            "URL",
            "GOLD",
            "NLCD PRF=%.2f;%.2f;%.2f" % methods_out[0][0],
            "NLCD ERROR",
            "NP PRF=%.2f;%.2f;%.2f" % methods_out[1][0],
            "NP ERROR",
            "CSE PRF=%.2f;%.2f;%.2f" % methods_out[2][0],
            "CSE ERROR",
        ])

        for i in xrange(len(gold_out)):

            eval_csv.writerow([
                str(i),
                gold_entries[i][0],

                gold_out[i],

                methods_out[0][1][i][0],
                str(methods_out[0][1][i][1]),

                methods_out[1][1][i][0],
                str(methods_out[1][1][i][1]),

                methods_out[2][1][i][0],
                str(methods_out[2][1][i][1]),

            ])


def step_3_eval_sources(args):

    """Evaluate titles extraction."""

    o_eval_fp = os.path.join(args.work_dir, "eval_source.csv")
    documents_db_path = os.path.join(args.work_dir, DOCUMENTS_DB_PATH)
    documents_db = husky.db.open(documents_db_path)
    eval_data = []

    extractor = EntityExtractor()

    with open(args.gold, "rb") as i_gold:

        gold_entries = csv.reader(i_gold, delimiter=",", quotechar="\"")
        gold_entries.next()
        gold_entries = list(gold_entries)

        for i, entry in enumerate(gold_entries):

            if i > 15:
                break

            url = entry[0]

            html = documents_db.get(url)
            article = extractor.parse_article(url, html)

            # Gold
            gold_sources = entry[3]

            # NLCD
            nlcd_sources = extractor.extract_sources(article, None, url)

            # Newspaper
            np_sources  = None#article.brand

            # CSE
            cse_sources = None

            eval_data.append((gold_sources, nlcd_sources, np_sources, cse_sources))

    gold_out, methods_out = husky.eval.compute_sources_prf(eval_data)

    with open(o_eval_fp, "wb") as o_eval:

        eval_csv = csv.writer(o_eval, delimiter=",", quotechar="\"")

        eval_csv.writerow([
            "#",
            "URL",
            "GOLD",
            "NLCD PRF=%.2f;%.2f;%.2f" % methods_out[0][0],
            "NLCD ERROR",
            "NP PRF=%.2f;%.2f;%.2f" % methods_out[1][0],
            "NP ERROR",
            "CSE PRF=%.2f;%.2f;%.2f" % methods_out[2][0],
            "CSE ERROR",
        ])

        for i in xrange(len(gold_out)):

            eval_csv.writerow([
                str(i),
                gold_entries[i][0],

                gold_out[i],

                methods_out[0][1][i][0],
                str(methods_out[0][1][i][1]),

                methods_out[1][1][i][0],
                str(methods_out[1][1][i][1]),

                methods_out[2][1][i][0],
                str(methods_out[2][1][i][1]),

            ])




STEPS = (
    (step_1_init_work_dir, "Prepare data for evaluating."),
    (step_2_eval_titles, "Evaluate titles extraction."),
    (step_3_eval_sources, "Evaluate sources extraction.")
)




if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("-v",
                           "--verbosity-level",
                           type=int,
                           default=1,
                           choices=(0, 1, 2))

    argparser.add_argument("--app-root",
                           type=str,
                           help="Directory containing processing package (e.g. `fenrir`).",
                           default=None)

    argparser.add_argument("--work-dir",
                           type=str,
                           help="Directory for storing temporary data for processing.",
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

    argparser.add_argument("--gold",
                           type=str,
                           help="Path to the gold standard file for dates normalization.",
                           default=None)

    argparser.add_argument("--cse",
                           type=str,
                           help="Path to JSON file with Google CSE annotations.",
                           default=None)

    argparser.add_argument("--eval-path",
                           type=str,
                           help="Path to the evaluation results for dates normalization.",
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

    # Turn-off third party loggers
    logging.getLogger("requests").setLevel(logging.WARNING)

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



























# def step_6_extract_related_gse_annotations(args):
#     """
#     Extract Google search engine annotations.
#     """

#     related_links_dir = os.path.join(args.work_dir, RELATED_LINKS_DIR)
#     related_gse_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)

#     extractor = EntityExtractor()
#     origins = read_origins(args)


#     clean_directory(related_gse_annotations_dir)


#     for i, url in enumerate(origins):

#         i_links_fp = os.path.join(related_links_dir, "%d.json" % i)
#         o_annotations_fp = os.path.join(related_gse_annotations_dir, "%d.json" % i)

#         with open(i_links_fp, "rb") as i_fl:
#             link_entries = json.load(i_fl)


#         for link_entry in link_entries:

#             gse_data = link_entry["gseData"]
#             annotation = extractor.get

#             # with open(related_annotations_json_fp, "wb") as o_fl:
#             #     # url = article["url"].encode("utf-8")
#             #     # title = article["title"].encode("utf-8")
#             #     # lang_id = article["lang_id"].encode("utf-8")
#             #     filtered_sentences = article["filteredSentences"]
#             #     annotations = {}
#             #     for sentence_entry in filtered_sentences:
#             #         sent_total_results = sentence_entry["totalResults"]
#             #         sent_api_response = sentence_entry["apiResponse"]
#             #         if sent_total_results == 0:
#             #             continue
#             #         for related_item in sent_api_response["items"]:
#             #             annotation = annotations_extractor.annotate(related_item)
#             #             if annotation.url in annotations:
#             #                 continue
#             #             annotations[annotation.url] = {
#             #                 "url": annotation.url,
#             #                 "title": annotation.title,
#             #                 "authors": annotation.authors,
#             #                 "source": annotation.sources,
#             #                 "dates": annotation.dates,
#             #                 "images": annotation.images,
#             #             }
#             #     json.dump(annotations.values(), o_fl, indent=4, sort_keys=False)


# def step_7_fetch_related_pages(args):
#     """Fetch related pages.
#     """
#     origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
#     related_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)
#     related_pages_database_dir = os.path.join(args.work_dir, RELATED_FULL_DATA_DIR)
#     if os.path.exists(related_annotations_dir):
#         logging.info("Cleaning previous related pages directory %s" % related_pages_database_dir)
#         rm_cmd = "rm -rf %s" % related_pages_database_dir
#         os.system(rm_cmd)
#     logging.info("Creating related pages directory: %s" % related_pages_database_dir)
#     os.mkdir(related_pages_database_dir)
#     with open(origins_fl, "rb") as fl:
#         origin_urls = fl.read().rstrip().split("\n")
#         logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
#     fetcher = husky.fetchers.PageFetcher()
#     related_data_ldb = husky.db.create(related_pages_database_dir)
#     urls = []
#     for i, url in enumerate(origin_urls):
#         related_annotations_json_fp = os.path.join(related_annotations_dir, "%d.json" % i)
#         logging.info("Loading related annotation from from (%d): %s" % (i, related_annotations_json_fp))
#         with open(related_annotations_json_fp, "rb") as i_fl:
#             annotations = json.load(i_fl)
#             for related_item in annotations:
#                 url = related_item["url"].encode("utf-8")
#                 urls.append(url)
#                 related_data_ldb.put("json+%s" % url, json.dumps(related_item))
#     async_related_list = fetcher.fetch_documents(urls, max_threads=args.max_threads)
#     def save_html(j_response):
#         try:
#             j, response = j_response
#             if j % 10 == 0 and j > 0:
#                 logging.info("Added %d/%d." % (len(urls), j+1))
#             html = fetcher.response_to_utf_8(response)
#             if args.use_compression == 1:
#                 html = lz4.compressHC(html)
#             if response.history is not None and len(response.history) > 0:
#                 url = response.history[0].url.encode("utf-8")
#             else:
#                 url = response.url.encode("utf-8")
#         except Exception:
#             return
#         related_data_ldb.put("html+%s" % url, html)
#     map(save_html, enumerate(async_related_list))
#     related_data_ldb.close()
#     logging.info("Added %d/%d." % (len(urls), len(urls)))
#     logging.info("Fetching completed.")


# def step_8_extract_full_annotations(args):
#     """Extract full annotations from related pages HTML.
#     """
#     origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
#     related_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)
#     related_pages_dir = os.path.join(args.work_dir, RELATED_FULL_DATA_DIR)
#     related_full_annotations_dir = os.path.join(args.work_dir, RELATED_FULL_ANNOTATIONS_DIR)
#     if os.path.exists(related_full_annotations_dir):
#         logging.info("Cleaning previous full annotations directory %s" % related_full_annotations_dir)
#         rm_cmd = "rm -rf %s" % related_full_annotations_dir
#         os.system(rm_cmd)
#     logging.info("Creating full annotations directory: %s" % related_full_annotations_dir)
#     os.mkdir(related_full_annotations_dir)
#     with open(origins_fl, "rb") as fl:
#         origin_urls = fl.read().rstrip().split("\n")
#         logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
#     annotator = EntityExtractor()
#     annotations_cache = {}
#     for i, url in enumerate(origin_urls):
#         related_annotations_json_fp = os.path.join(related_annotations_dir, "%d.json" % i)
#         related_htmls_database_dir = os.path.join(related_pages_dir, "%d.ldb" % i)
#         related_full_annotations_json_fp = os.path.join(related_full_annotations_dir, "%d.json" % i)
#         logging.info("Loading related annotation from from (%d): %s" % (i, related_annotations_json_fp))
#         with open(related_annotations_json_fp, "rb") as i_fl:
#             annotations = json.load(i_fl)
#             related_htmls_ldb = husky.db.open(related_htmls_database_dir)
#             with open(related_full_annotations_json_fp, "wb") as o_fl:
#                 for annotation in annotations["relatedArticlesAnnotations"]:
#                     items = annotation["relatedItems"]
#                     for j, item in enumerate(items):
#                         logging.info("Processing %d of %d item." % (j+1, len(items)))
#                         url = item["url"].encode("utf-8")

#                         if url in annotations_cache:
#                             item_annotation = annotations_cache[url]
#                         else:
#                             html = related_htmls_ldb.get(url)
#                             if args.use_compression == 1:
#                                 try:
#                                     html = lz4.decompress(html)
#                                 except Exception:
#                                     continue
#                             try:
#                                 item_annotation = annotator.annotate((url, html))
#                                 annotations_cache[url] = item_annotation
#                             except Exception:
#                                 import traceback
#                                 traceback.print_exc()
#                                 item_annotation = None

#                         if item_annotation is not None:
#                             item["title"] += item_annotation.title
#                             item["authors"] += item_annotation.authors
#                             item["source"] += item_annotation.sources
#                             item["dates"] += item_annotation.dates
#                             item["images"] += item_annotation.images


#                 json.dump(annotations, o_fl, indent=4, sort_keys=False)
#             related_htmls_ldb.close()


# def step_9_normalize_data(args):
#     """Extract full annotations from related pages HTML.
#     """
#     origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
#     related_full_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR) #TODO
#     normalized_annotations_dir = os.path.join(args.work_dir, NORMALIZED_ANNOTATIONS_DIR)
#     if os.path.exists(normalized_annotations_dir):
#         logging.info("Cleaning previous set_classified_data annotations directory %s" % normalized_annotations_dir)
#         rm_cmd = "rm -rf %s" % normalized_annotations_dir
#         os.system(rm_cmd)
#     logging.info("Creating set_classified_data annotations directory: %s" % normalized_annotations_dir)
#     os.mkdir(normalized_annotations_dir)
#     with open(origins_fl, "rb") as fl:
#         origin_urls = fl.read().rstrip().split("\n")
#         logging.info("Loaded %d urls from %s." % (len(origin_urls), origins_fl))
#     normalizer = husky.norm.pattern.ArticleNormalizer()
#     dates = {}
#     authors = {}
#     normalized_titles_fp = os.path.join(normalized_annotations_dir, "titles.csv")
#     normalized_authors_fp = os.path.join(normalized_annotations_dir, "authors.csv")
#     normalized_sources_fp = os.path.join(normalized_annotations_dir, "sources.csv")
#     normalized_dates_fp = os.path.join(normalized_annotations_dir, "dates.csv")
#     with open(normalized_titles_fp, "wb") as titles_fl, \
#          open(normalized_authors_fp, "wb") as authors_fl, \
#          open(normalized_sources_fp, "wb") as sources_fl, \
#          open(normalized_dates_fp, "wb") as dates_fl:
#         for i, url in enumerate(origin_urls):
#             related_full_annotations_json_fp = os.path.join(related_full_annotations_dir, "%d.json" % i)
#             normalized_annotations_json_fp = os.path.join(normalized_annotations_dir, "%d.json" % i)

#             with open(related_full_annotations_json_fp, "rb") as full_annotations_fl, \
#                  open(normalized_annotations_json_fp, "wb") as normalized_annotations_fl:
#                 annotations = json.load(full_annotations_fl)

#                 for annotation in annotations["relatedArticlesAnnotations"]:
#                     items = annotation["relatedItems"]

#                     for j, item in enumerate(items):

#                         for date in item["dates"]:
#                             dates[date] = normalizer.classify_author_string(date)
#                         for author in item["authors"]:
#                             authors[author] = normalizer.normalize_author(author)

#                         item["dates"] = normalizer.normalize(item["dates"])
#                         item["authors"] = normalizer.normalize_authors(item["authors"])

#         for date, norm_date in sorted(dates.items(), key=lambda x: x[1]):
#             dates_fl.write("%s\t%s\n" % (date.encode("utf-8"), norm_date.encode("utf-8")))
#         for author, norm_author in sorted(authors.items(), key=lambda x: x[1]):
#             authors_fl.write("%s\t\t\t%r\n" % (author.encode("utf-8"), ""))


# def step_10_evalualte_ner(args):
#
#     related_annotations_dir = os.path.join(args.work_dir, RELATED_GSE_ANNOTATIONS_DIR)
#     origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
#     input_documents_dir = os.path.join(args.work_dir, RELATED_FULL_DATA_DIR)
#     html_db = husky.db.open(input_documents_dir).prefixed_db("html+")
#     search_annotations = {}
#     site_blacklist = husky.dicts.Blacklist.load(husky.dicts.Blacklist.BLACK_DOM)
#
#     fetcher = husky.fetchers.PageFetcher()
#     extractor = EntityExtractor()
#     normalizer = EntityNormalizer()
#
#     output_eval_dates_fl = os.path.join(args.eval_extr, "eval.date.csv")
#     output_eval_authors_fl = os.path.join(args.eval_extr, "eval.author.csv")
#
#     # Collect Search annotations.
#     with open(origins_fl, "rb") as fl:
#         origin_urls = fl.read().rstrip().split("\n")
#     for i, url in enumerate(origin_urls):
#         related_annotations_json_fp = os.path.join(related_annotations_dir, "%d.json" % i)
#         with open(related_annotations_json_fp, "rb") as i_fl:
#             annotations = json.load(i_fl)
#             for related_item in annotations:
#                 url = related_item["url"].encode("utf-8")
#                 search_annotations[url] = related_item
#
#     eval_entries = []
#     with open(args.gold_extr, "rb") as i_gold:
#         csv_reader = csv.reader(i_gold, delimiter=",", quotechar="\"")
#         next(csv_reader, None)
#
#         for url, true_authors, true_dates in csv_reader:
#
#             true_authors = set() if true_authors == "<NONE>" else set(true_authors.lower().strip().split(" and "))
#             true_dates = set() if true_dates == "<NONE>" else set(true_dates.lower().strip().split(" and "))
#
#             pred_authors, pred_dates = None, None
#
#             # Check if url is blacklisted
#             if url in site_blacklist:
#                 pred_authors, pred_dates = [], []
#                 eval_entries.append((url, true_authors, true_dates, pred_authors, pred_dates))
#                 continue
#
#             # Try to get HTML of url
#             try:
#                 html = html_db.get(url)
#                 html = lz4.decompress(html) if args.use_compression == 1 else html
#             except TypeError:
#                 logging.warning("HTML is not found. Skip %r." % url)
#                 try:
#                     html = fetcher.fetch(url)
#                 except Exception:
#                     logging.warning("HTML is not downloaded. Skip %r." % url)
#                     html = "<html></html>"
#
#             # Try to parse article
#             try:
#                 article = extractor.parse_article(url, html)
#             except Exception:
#                 logging.warning("HTML cannot be parsed. Skip %r." % url)
#                 pred_authors, pred_dates = [], []
#                 eval_entries.append((url, true_authors, true_dates, pred_authors, pred_dates))
#                 continue
#
#             # Try find annotation
#             try:
#                 annotation = search_annotations[url]
#             except Exception:
#                 logging.warning("Annotation is not found. %r" % url)
#                 annotation = None
#                 pred_dates = []
#
#             if pred_dates is None:
#                 try:
#                     raw_dates = annotation["dates"]
#                     pred_dates = normalizer.normalize_dates(raw_dates)
#                     if len(pred_dates) > 1:
#                         pred_dates = [min(pred_dates)]
#                     pred_dates = set((d.lower() for d in pred_dates))
#                 except Exception:
#                     logging.warning("Error when extracting dates. %r" % url)
#                     pred_dates = set()
#
#             if pred_authors is None:
#                 try:
#                     raw_authors = extractor.extract_authors(article, annotation)
#                     pred_authors = normalizer.normalize_authors(raw_authors, article=article)
#                     pred_authors = set((a.name.lower() for a in pred_authors))
#                 except Exception:
#                     logging.warning("Error when extracting authors. %r" % url)
#                     pred_authors = set()
#
#             eval_entries.append((url, true_authors, true_dates, pred_authors, pred_dates))
#
#     authors_arp, authors_errors = husky.evaluation.compute_arp(((e[1], e[3]) for e in eval_entries))
#     dates_arp, dates_errors = husky.evaluation.compute_arp(((e[2], e[4]) for e in eval_entries))
#
#     # Write dates eval file.
#     out_entries = [(e[0], e[2], e[4], err) for e, err in zip(eval_entries, dates_errors)]
#     out_entries.sort(key=lambda row: row[-1])
#     out_sorted = []
#     for url, true_val, pred_val, errors in out_entries:
#         true_val = "<NONE>" if len(true_val) == 0 else " AND ".join(sorted(true_val))
#         pred_val = "<NONE>" if len(pred_val) == 0 else " AND ".join(sorted(pred_val))
#         out_sorted.append((url, true_val, pred_val, errors))
#     out_sorted = [("Url (P=%4f; R=%.4f; A=%.4f)." % dates_arp, "True Value", "Extr. Value", "Errors")] + out_sorted
#     with open(output_eval_dates_fl, "wb") as fl:
#         csv_writer = csv.writer(fl, delimiter=",", quotechar="\"")
#         csv_writer.writerows(out_sorted)
#
#     # Write authors eval file.
#     out_entries = [(e[0], e[1], e[3], err) for e, err in zip(eval_entries, authors_errors)]
#     out_entries.sort(key=lambda row: row[-1])
#     out_sorted = []
#     for url, true_val, pred_val, errors in out_entries:
#         true_val = "<NONE>" if len(true_val) == 0 else " AND ".join(sorted(true_val))
#         pred_val = "<NONE>" if len(pred_val) == 0 else " AND ".join(sorted(pred_val))
#         out_sorted.append((url, true_val, pred_val, errors))
#     out_sorted = [("Url (P=%4f; R=%.4f; A=%.4f)." % authors_arp, "True Value", "Extr. Value", "Errors")] + out_sorted
#     with open(output_eval_authors_fl, "wb") as fl:
#         csv_writer = csv.writer(fl, delimiter=",", quotechar="\"")
#         csv_writer.writerows(out_sorted)