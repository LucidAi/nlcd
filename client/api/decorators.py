# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import json
import datetime
import traceback

from django.http import HttpResponse

from client.api import common


def nlcd_api_call(request_function):

    def wrapped_api_call(request):

        ts_begin = datetime.datetime.now()

        try:
            response_data_dict = request_function(request)
            error_code = 0
            debug_str = ""
            http_code = 200
        except common.NlcdApi400Error:
            response_data_dict = None
            error_code = 1
            debug_str = traceback.format_exc()
            http_code = 400
        except common.NlcdApi500Error:
            response_data_dict = None
            error_code = 2
            debug_str = traceback.format_exc()
            http_code = 500
        except common.NlcdApi501Error:
            response_data_dict = None
            error_code = 3
            debug_str = traceback.format_exc()
            http_code = 501
        except common.NlcdApi503Error:
            response_data_dict = None
            error_code = 4
            debug_str = traceback.format_exc()
            http_code = 503
        except Exception:
            response_data_dict = None
            error_code = 5
            debug_str = traceback.format_exc()
            http_code = 500

        ts_end = datetime.datetime.now()

        response = {
            "errorCode":        error_code,
            "errorStr":         "",
            "debugStr":         debug_str,
            "data":             response_data_dict,
            "beginTime":        common.format_iso_datetine(ts_begin),
            "endTime":          common.format_iso_datetine(ts_end),
            "durationTime":     str(ts_end - ts_begin),
        }

        json_str = json.dumps(response, sort_keys=True)

        return HttpResponse(json_str,
                            content_type="application/json",
                            status=http_code)

    return wrapped_api_call
