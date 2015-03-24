# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from client.api.decorators import nlcd_api_call
from husky.tpas import create_api


@csrf_exempt
@nlcd_api_call
def get_test_graph(request):

    graph_id = request.GET["graphId"]

    with open("webapp/json/%s.json" % graph_id, "rb") as i_fl:
        graph = json.load(i_fl)

    return graph


@csrf_exempt
@nlcd_api_call
def tpas_engine_list(request):
    credentials = settings.NLCD_CONF["credentials"]
    engines = []
    for engine_id, engine_data in credentials.iteritems():
        engines.append({
            "eId": engine_id,
        })
    return {
        "engines": engines,
    }

@csrf_exempt
@nlcd_api_call
def tpas_engine_call(request):
    query_text = request.GET.get("queryText", "")
    control_engine_id = request.GET.get("controlEngine")
    engines_id = request.GET.get("treatmentEngines", "").split(",")
    credentials = settings.NLCD_CONF["credentials"]


    control_engine = create_api(credentials, control_engine_id)
    control_query = control_engine.make_query(query_string=query_text, exact_terms=query_text)
    control, _, _ = control_engine.find_results(control_query)

    # treatments = []
    # for engine_id in engines_id:
    #     engine =  create_api(credentials, engine_id)
    #     query = engine.make_query(query_string=query_text)
    #     found_results, _, _ = engine.find_results(query)
    #     treatments.append(found_results)

    return {
        "control"       : control,
        # "treatments"    : treatments,
    }
