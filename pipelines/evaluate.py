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