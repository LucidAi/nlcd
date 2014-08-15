#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import os
import sys
import json
import logging
import argparse
import datetime
import collections

import husky.db
import husky.api.google

from husky.dicts import Blacklist
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
RELATED_LINKS_DIR               = "6.related_links"
CROSSREF_IN_DATA_DIR            = "7.crossref_in"
CROSSREF_OUT_DATA_DIR           = "8.crossref_out"
STORY_GRAPH_DIR                 = "9.story_graph"


def clean_directory(path):
    """
    Create path if not exist otherwise recreates it.
    """
    if os.path.exists(path):
        os.system("rm -rf %s" % path)
    os.mkdir(path)


def to_utf_8_dict(data):
    """
    Encode string values found in `data` into utf-8 unicode.
    """
    if isinstance(data, unicode):
        return data.encode("utf-8")
    if isinstance(data, str):
        try:
            unicode_data = data.decode("utf-8")
            return data
        except:
            unicode_data = data.decode("latin-1")
            return unicode_data.encode("utf-8")
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


def json_dump(obj, fp):
    """
    Write object in JSON format to file stream fp.
    """
    fp.write(json.dumps(to_utf_8_dict(obj), indent=4, ensure_ascii=False, encoding="utf-8"))


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


def step_3_extract_origin_bodies(args):
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

                logging.info("Saving GSE with %d unique links." % len(unique_links))
                json_dump(origin_gse, o_fl)


def step_6_filter_out_unrelated(args):
    """
    Filter not related documents found by Google.
    """

    origin_gse_dir = os.path.join(args.work_dir, ORIGIN_GSE_DIR)
    related_links_dir = os.path.join(args.work_dir, RELATED_LINKS_DIR)
    origins = read_origins(args)
    black_domains = Blacklist.load(Blacklist.BLACK_DOM)
    fetcher = PageFetcher()
    text_util = TextUtil()

    clean_directory(related_links_dir)

    for i, url in enumerate(origins):

        i_gse_fp = os.path.join(origin_gse_dir, "%d.json" % i)
        o_link_fp = os.path.join(related_links_dir, "%d.json" % i)

        related_url2gse = {}    # Google search annotation for each URL
        related_url2html = {}   # HTML for related URL
        related_url2segm = {}   # all "linked" sentences for related URL

        uniq_segments = set()

        with open(i_gse_fp, "rb") as i_fl:
            gse = json.load(i_fl)

        for segment_entry in gse:

            segment_text = text_util.simplified_text(segment_entry["segment"])
            uniq_segments.add(segment_text)

            for gse_found_item in segment_entry["foundItems"]:

                item_url = gse_found_item["link"]

                if item_url in black_domains:
                    # logging.warn("Blacklisted related url %s" % item_url)
                    continue

                if item_url not in related_url2gse:
                    related_url2gse[item_url] = gse_found_item

                if item_url not in related_url2segm:
                    related_url2segm[item_url] = {segment_text}
                else:
                    related_url2segm[item_url].add(segment_text)

                if item_url not in related_url2html:
                    related_url2html[item_url] = None


        fetcher.fetch_urls(related_url2html, max_threads=args.max_threads)

        # Now, filter not related

        # 1. Put all fetched urls into related set
        related_urls = set(related_url2html.iterkeys())

        filtered_urls = []

        fuzzy_patterns = text_util.compile_fuzzy_patterns(uniq_segments)

        for j, rel_url in enumerate(related_urls):

            if j % 10 == 0:
                logging.info("Fuzzy matching %d/%d" % (j, len(related_urls)))

            html = related_url2html[rel_url]
            body, _ = text_util.extract_body(rel_url, html)
            body = text_util.simplified_text(body)
            segments = related_url2segm[rel_url]

            best_ratio = 0.0
            matches = []

            for segment in segments:

                fuzzy_pattern = fuzzy_patterns[segment]
                ratio, match = text_util.fuzzy_search(body, segment, fuzzy_pattern)
                matches.append({
                    "match": match,
                    "ratio": ratio,
                })

                if ratio > best_ratio:
                    best_ratio = ratio

            gse_data = related_url2gse[rel_url]

            filtered_urls.append({
                "url": rel_url,
                "segments": list(segments),
                "body": body,
                "bestRatio": best_ratio,
                "foundMatches": matches,
                "highRatio": best_ratio > 0.5,
                "gseData": gse_data,
                "html": html,
            })

        with open(o_link_fp, "wb") as o_fl:
            json_dump(filtered_urls, o_fl)


def step_7_gen_cr_data(args):
    """
    Generate data for cress-reference detection
    """

    related_links_dir = os.path.join(args.work_dir, RELATED_LINKS_DIR)
    crossref_data_in_dir = os.path.join(args.work_dir, CROSSREF_IN_DATA_DIR)


    origins = read_origins(args)

    fetcher = PageFetcher()
    extractor = EntityExtractor()
    normalizer = EntityNormalizer()
    blacklist = husky.dicts.Blacklist.load(husky.dicts.Blacklist.BLACK_DOM)

    clean_directory(crossref_data_in_dir)

    for i, _ in enumerate(origins):

        # File with related annotations for given origin.
        i_links_fp = os.path.join(related_links_dir, "%d.json" % i)
        o_crossref_fp = os.path.join(crossref_data_in_dir, "%d.json" % i)

        annotation_id = 1
        output_data = []

        with open(i_links_fp, "rb") as i_fl:
            link_entries = json.load(i_fl)

        for link_entry in link_entries:

            if not link_entry["highRatio"]:
                continue

            url = link_entry["url"].encode("utf-8")
            body = link_entry["body"].encode("utf-8")

            # Check if url is Blacklisted
            if url in blacklist:
                continue

            # 1. Get html
            html = link_entry["html"]

            # Parse article.
            try:
                article = extractor.parse_article(url, html)
            except Exception:
                logging.warning("HTML cannot be parsed. Skip %r." % url)
                continue

            # Get searcher data
            gse_data = link_entry["gseData"]

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
            sources = extractor.extract_sources(annotation=gse_data)
            sources = list(set((s.lower() for s in sources)))

            # 5. Extract publication dates
            try:
                raw_dates = extractor.extract_dates(annotation=gse_data)
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
                raw_authors = extractor.extract_authors(article, annotation=gse_data)
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
                "body": body,
            })

        with open(o_crossref_fp, "wb") as o_fl:
            logging.info("Saving %d annotated entries." % len(output_data))
            json_dump(output_data, o_fl)


def step_8_find_cross_references(args):
    """
    """

    origins_fl = os.path.join(args.work_dir, ORIGIN_URL_FILE)
    input_documents_dir = os.path.join(args.work_dir, CROSSREF_IN_DATA_DIR)
    output_documents_dir = os.path.join(args.work_dir, CROSSREF_OUT_DATA_DIR)

    clean_directory(output_documents_dir)

    with open(origins_fl, "rb") as fl:
        origin_urls = fl.read().rstrip().split("\n")

    for i, origin_url in enumerate(origin_urls):

        i_documents_fp = os.path.join(input_documents_dir, "%d.json" % i)
        o_graph_fp = os.path.join(output_documents_dir, "%d.json" % i)

        with open(i_documents_fp, "rb") as i_fl:
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
                body=article_data.get("body").encode("utf-8")
            )

        ref_index = ReferenceIndex((read_ref_entry(article) for article in articles))

        ref_index.print_titles()
        ref_index.index()

        found_links = ref_index.find_cross_references(sent_window_size=3)

        graph_edges = []
        graph_nodes = {}

        for pair in found_links:
            graph_edges.append(list(pair))

        for entry in ref_index.iterentries():
            graph_nodes[entry.ref_id] = {
                "refId": entry.ref_id,
                "url": entry.url,
                "text": entry.text,
                "title": entry.title,
                "sources": entry.sources,
                "pubDate": entry.pub_date.strftime("%Y.%m.%d") if entry.pub_date is not None else None,
                "authors": entry.authors,
                "body": entry.body,
            }

        graph = {"nodes": graph_nodes, "edges": graph_edges}

        with open(o_graph_fp, "wb") as o_fl:
            json_dump(graph, o_fl)


def step_9_enrich_story_graphs(args):

    origins = read_origins(args)

    graph_dir = os.path.join(args.work_dir, CROSSREF_OUT_DATA_DIR)
    story_dir = os.path.join(args.work_dir, STORY_GRAPH_DIR)

    clean_directory(story_dir)

    fetcher = PageFetcher()
    textutil = TextUtil()

    for i, origin_url in enumerate(origins):

        # if i != 4:
        #     continue

        logging.info("Processing graph #%d" % i)

        graph_fp = os.path.join(graph_dir, "%d.json" % i)
        story_fp = os.path.join(story_dir, "%d.json" % i)

        with open(graph_fp, "rb") as graph_fl:
            graph = json.load(graph_fl)

        # Pre-process edges
        edges = set()
        for a, b in graph["edges"]:
            edges.add((min(a, b), max(a, b)))
        ref_counter = collections.Counter()
        for a, b in edges:
            ref_counter[a] += 1
            ref_counter[b] += 1

        # Find central reference, also index by url
        central_ref_id = None

        url_index = {}
        for node in graph["nodes"].itervalues():
            node_url = node["url"]
            url_index[node_url] = node
            if node_url == origin_url:
                central_ref_id = node["refId"]

        if central_ref_id is None:
            logging.warn("Central reference not found. Selecting the most referenced.")
            central_ref_id = ref_counter.most_common(1)[0][0]
            logging.info(central_ref_id)

        urls = [node["url"] for node in graph["nodes"].itervalues()]

        # Download FB reactions
        fb_counts = fetcher.get_facebool_counts(urls)
        logging.info("Fetched %d FB reactions" % len([fc for fc in fb_counts if fc is not None]))
        fb_comments = {}
        fb_shares = {}
        for fb_entry in (fc for fc in fb_counts if fc is not None):
            n_comments = fb_entry.get("comments", 0)
            n_shares = fb_entry.get("shares", 0)
            ref_id = url_index[fb_entry["id"]]["refId"]
            fb_comments[ref_id] = n_comments
            fb_shares[ref_id] = n_shares

        # Download TW reactions
        tw_counts = fetcher.get_twitter_counts(urls)
        logging.info("Fetched %d TW reactions" % len([te for te in tw_counts if te is not None]))
        tw_shares = {}
        for tw_entry in (te for te in tw_counts if te is not None):
            n_shares = tw_entry.get("count", 0)
            tw_url = tw_entry["url"]
            node = url_index.get(tw_url)
            if node is None:
                node = url_index.get(tw_url[:-1])
                if node is None:
                    continue
            ref_id = node["refId"]
            tw_shares[ref_id] = n_shares

        # Generate date distribution

        # Find additional connection features

        nodes = {}

        author2refs = {}
        author2sources = {}

        source2refs = {}
        source2authors = {}

        for node in graph["nodes"].itervalues():

            ref_id = node["refId"]

            node["twitterShares"] = tw_shares.get(ref_id, 0)
            node["facebookShares"] = fb_shares.get(ref_id, 0)
            node["facebookComments"] = fb_comments.get(ref_id, 0)
            node["referenceCount"] = ref_counter.get(ref_id, 0)
            node["citationCount"] = 0
            node["shareCount"] = node["twitterShares"] + node["facebookShares"]

            nodes[node["refId"]] = node

            node["authors"] = sorted(node["authors"])
            node["sources"] = list(reversed(sorted(node["sources"])))

            source = None
            if len(node["sources"]) > 0:
                source = node["sources"][0]

            for author in node["authors"]:
                if author not in author2refs:
                    author2refs[author] = {ref_id}
                else:
                    author2refs[author].add(ref_id)
                if source is not None:
                    if author not in author2sources:
                        author2sources[author] = {source}
                    else:
                        author2sources[author].add(source)

            if source is not None:

                if source not in source2refs:
                    source2refs[source] = {ref_id}
                else:
                    source2refs[source].add(ref_id)

                if source not in source2authors:
                    source2authors[source] = set(node["authors"])
                else:
                    source2authors[source].update(node["authors"])

        authors = []
        sources = []

        for author, references in author2refs.iteritems():
            authors.append({
                "name": author,
                "referenceCount": len(references),
                "references": list(references),
                "authors": list(author2sources.get(author, []))
            })

        for source, references in source2refs.iteritems():
            sources.append({
                "name": source,
                "referenceCount": len(references),
                "references": list(references),
                "authors": list(source2authors.get(source, []))
            })

        edges = list(edges)

        html = fetcher.fetch(nodes[central_ref_id]["url"])
        paragraphs = textutil.get_pretty_markup(html)
        paragraphs = [p.encode("utf-8") for p in paragraphs]

        bodies = [(node["body"].encode("utf-8"), node["refId"])
                   for node in nodes.itervalues()
                   if node["refId"] != central_ref_id]

        # text_markup = [textutil.generate_markup(p_text, bodies)  for p_text in paragraphs]
        text = nodes[central_ref_id]["text"].encode("utf-8")
        title = nodes[central_ref_id]["title"].encode("utf-8")
        markup = textutil.generate_markup(title, text, paragraphs, bodies)

        story_graph = {

            "edges": edges,
            "nodes": nodes,
            "meta": {
                "centralNode": central_ref_id,
                "citations": [],
                "markup": markup.json(),
                "authors": authors,
                "sources": sources,
            }

        }

        story_fp = os.path.join(story_dir, "%d.json" % i)

        with open(story_fp, "wb") as o_fl:
            json_dump(story_graph, o_fl)


STEPS = (
    (step_1_init_work_dir, "Prepare data for processing."),
    (step_2_fetch_origin_articles, "Fetch origin articles."),
    (step_3_extract_origin_bodies, "Extract origin content bodies."),
    (step_4_extract_sentences, "Extract sentences/segments."),
    (step_5_request_gse, "Fetch related links from Google Search."),
    (step_6_filter_out_unrelated, "Filter unrelated links."),
    (step_7_gen_cr_data, "Generate data for cross-reference detection."),
    (step_8_find_cross_references, "Find references between related articles."),
    (step_9_enrich_story_graphs, "Enrich story graphs"),
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
