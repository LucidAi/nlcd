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

from husky.entity import Entity
from husky.fetchers import PageFetcher
from husky.extraction import EntityExtractor
from husky.extraction import EntityNormalizer


DOCUMENTS_DB_PATH = "documents.ldb"


def clean_directory(path):
    """
    Create path if not exist otherwise recreates it.
    """
    if os.path.exists(path):
        os.system("rm -rf %s" % path)
    os.mkdir(path)


def u(i_str):
    """
    Encode string values found in `data` into utf-8 unicode.
    """
    if i_str is None:
        return ""
    if isinstance(i_str, unicode):
        return i_str.encode("utf-8")
    try:
        unicode_data = i_str.decode("utf-8")
        return i_str
    except Exception:
        unicode_data = i_str.decode("latin-1")
        return unicode_data.encode("utf-8")


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

    with open(args.gold, "rb") as i_gold:

        gold_entries = csv.reader(i_gold, delimiter=",", quotechar="\"")
        gold_entries.next()
        gold_entries = list(gold_entries)

        for i, entry in enumerate(gold_entries):


            url = entry[0]
            cse_entry = cse.get(url)

            logging.info("Processing url: %r" % url)

            if cse_entry is None:
                logging.warn("URL #%d not found in CSE annotations: %s\nSkip." % (i, url))
                continue

            html = documents_db.get(url)

            if html is None or len(html) == 0:
                logging.error("URL #%d not found in HTML db: %s." % (i, url))
                continue

            try:
                article = extractor.parse_article(url, html)
            except Exception:
                logging.error("URL #%d error while parsing: %s." % (i, url))
                continue

            # Gold
            gold_title = entry[1]

            # CSE
            cse_title = min(cse_entry["title"], key=len) if len(cse_entry["title"]) > 0 else None

            # NLCD
            nlcd_title = cse_title
            if nlcd_title is None:
                nlcd_title = extractor.extract_titles(article, None, select_best=True)

            # Newspaper
            np_title = article.title


            eval_data.append((gold_title, nlcd_title, np_title, cse_title))


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

                u(gold_out[i]),

                u(methods_out[0][1][i][0]),
                u(methods_out[0][1][i][1]),

                u(methods_out[1][1][i][0]),
                u(methods_out[1][1][i][1]),

                u(methods_out[2][1][i][0]),
                u(methods_out[2][1][i][1]),

            ])


def step_3_eval_authors(args):
    """Evaluate authors extraction."""

    o_eval_fp = os.path.join(args.work_dir, "eval_authors.csv")
    documents_db_path = os.path.join(args.work_dir, DOCUMENTS_DB_PATH)
    documents_db = husky.db.open(documents_db_path)
    eval_data = []

    extractor = EntityExtractor()
    normalizer = EntityNormalizer()

    with open(args.cse, "rb") as cse_fl:
        cse = json.load(cse_fl)

    with open(args.gold, "rb") as i_gold:

        gold_entries = csv.reader(i_gold, delimiter=",", quotechar="\"")
        gold_entries.next()
        gold_entries = list(gold_entries)

        for i, entry in enumerate(gold_entries):

            url = entry[0]
            cse_entry = cse.get(url)

            logging.info("Processing url: %r" % url)

            if cse_entry is None:
                logging.warn("URL #%d not found in CSE annotations: %s\nSkip." % (i, url))
                continue

            html = documents_db.get(url)

            if html is None or len(html) == 0:
                logging.error("URL #%d not found in HTML db: %s." % (i, url))
                continue

            try:
                article = extractor.parse_article(url, html)
            except Exception:
                logging.error("URL #%d error while parsing: %s." % (i, url))
                continue

            # Gold
            gold_authors = entry[2]

            # CSE
            cse_authors = cse_entry["authors"]

            # NLCD
            try:
                entities = extractor.extract_authors(article, annotation=None)
                authors = normalizer.normalize_authors(entities, article=article)
                nlcd_authors = list(set((a.name for a in authors
                                         if a.ent_type == Entity.TYPE.PER
                                         and a.ent_rel == Entity.REL.AUTHOR)))
                if len(nlcd_authors) == 0:
                    entities = [Entity(raw=c) for c in cse_authors]
                    authors = normalizer.normalize_authors(entities, article=article)
                    nlcd_authors = list(set((a.name for a in authors
                                             if a.ent_type == Entity.TYPE.PER
                                             and a.ent_rel == Entity.REL.AUTHOR)))
            except Exception:
                logging.warning("Error when extracting authors. %r" % url)
                nlcd_authors = []

            # Newspaper
            np_authors = article.authors

            eval_data.append((gold_authors, nlcd_authors, np_authors, cse_authors))

    gold_out, methods_out = husky.eval.compute_authors_prf(eval_data)

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

                u(gold_out[i]),

                u(methods_out[0][1][i][0]),
                u(methods_out[0][1][i][1]),

                u(methods_out[1][1][i][0]),
                u(methods_out[1][1][i][1]),

                u(methods_out[2][1][i][0]),
                u(methods_out[2][1][i][1]),

            ])


def step_4_eval_source(args):
    """Evaluate sources extraction."""

    o_eval_fp = os.path.join(args.work_dir, "eval_sources.csv")
    documents_db_path = os.path.join(args.work_dir, DOCUMENTS_DB_PATH)
    documents_db = husky.db.open(documents_db_path)
    eval_data = []

    extractor = EntityExtractor()
    normalizer = EntityNormalizer()

    with open(args.cse, "rb") as cse_fl:
        cse = json.load(cse_fl)

    with open(args.gold, "rb") as i_gold:

        gold_entries = csv.reader(i_gold, delimiter=",", quotechar="\"")
        gold_entries.next()
        gold_entries = list(gold_entries)

        for i, entry in enumerate(gold_entries):

            url = entry[0]
            cse_entry = cse.get(url)

            logging.info("Processing url: %r" % url)

            if cse_entry is None:
                logging.warn("URL #%d not found in CSE annotations: %s\nSkip." % (i, url))
                continue

            html = documents_db.get(url)

            if html is None or len(html) == 0:
                logging.error("URL #%d not found in HTML db: %s." % (i, url))
                continue

            try:
                article = extractor.parse_article(url, html)
            except Exception:
                logging.error("URL #%d error while parsing: %s." % (i, url))
                continue

            # Gold
            gold_sources = entry[3]

            # CSE
            cse_sources = cse_entry["source"]

            # NLCD
            try:
                entities = extractor.extract_authors(article, annotation=None)
                entities = normalizer.normalize_authors(entities, article=article)
                nlcd_sources = list(set((e.name for e in entities
                                         if e.ent_rel == Entity.REL.SOURCE)))
            except Exception:
                logging.warning("Error when extracting authors. %r" % url)
                nlcd_sources = []

            nlcd_sources.extend(extractor.extract_sources(article, None, url))
            nlcd_sources.extend(cse_sources)

            # Newspaper
            np_sources = ["<N/A>"]

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

                u(gold_out[i]),

                u(methods_out[0][1][i][0]),
                u(methods_out[0][1][i][1]),

                u(methods_out[1][1][i][0]),
                u(methods_out[1][1][i][1]),

                u(methods_out[2][1][i][0]),
                u(methods_out[2][1][i][1]),

            ])


def step_5_eval_dates(args):
    """Evaluate dates extraction."""

    o_eval_fp = os.path.join(args.work_dir, "eval_dates.csv")
    documents_db_path = os.path.join(args.work_dir, DOCUMENTS_DB_PATH)
    documents_db = husky.db.open(documents_db_path)
    eval_data = []

    extractor = EntityExtractor()
    normalizer = EntityNormalizer()

    with open(args.cse, "rb") as cse_fl:
        cse = json.load(cse_fl)

    with open(args.gold, "rb") as i_gold:

        gold_entries = csv.reader(i_gold, delimiter=",", quotechar="\"")
        gold_entries.next()
        gold_entries = list(gold_entries)

        for i, entry in enumerate(gold_entries):

            url = entry[0]
            cse_entry = cse.get(url)

            if cse_entry is None:
                logging.warn("URL #%d not found in CSE annotations: %s\nSkip." % (i, url))
                continue

            # Gold
            gold_dates = entry[4]

            # CSE
            cse_dates = normalizer.normalize_dates(cse_entry["dates"])

            # NLCD
            nlcd_dates = cse_dates


            # Newspaper
            np_dates = ["<N/A>"]

            eval_data.append((gold_dates, nlcd_dates, np_dates, cse_dates))

    gold_out, methods_out = husky.eval.compute_dates_prf(eval_data)

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

                u(gold_out[i]),

                u(methods_out[0][1][i][0]),
                u(methods_out[0][1][i][1]),

                u(methods_out[1][1][i][0]),
                u(methods_out[1][1][i][1]),

                u(methods_out[2][1][i][0]),
                u(methods_out[2][1][i][1]),

            ])


STEPS = (
    (step_1_init_work_dir, "Prepare data for evaluating."),
    (step_2_eval_titles, "Evaluate titles extraction."),
    (step_3_eval_authors, "Evaluate authors extraction."),
    (step_4_eval_source, "Evaluate sources extraction."),
    (step_5_eval_dates, "Evaluate dates extraction."),
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
