# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from client.api.decorators import nlcd_api_call


@csrf_exempt
@nlcd_api_call
def get_test_graph(request):

    with open("webapp/json/5.json", "rb") as i_fl:
        graph = json.load(i_fl)

    return graph
