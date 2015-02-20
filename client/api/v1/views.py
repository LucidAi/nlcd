# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from client.api.decorators import nlcd_api_call

from husky.tpas import create_api


with open("conf/dev.json", "rb") as fl:
    nlcd_config = json.load(fl)

cse_api = create_api(nlcd_config["nlcd"]["tpas"]["api.GoogleCSE"])


@csrf_exempt
@nlcd_api_call
def get_test_graph(request):

    graph_id = request.GET["graphId"]

    with open("webapp/json/%s.json" % graph_id, "rb") as i_fl:
        graph = json.load(i_fl)

    return graph


@csrf_exempt
@nlcd_api_call
def tpas(request):

    return {}
