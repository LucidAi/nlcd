# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

from google import CseAPI as GoogleAPI
from faroo import FarooAPI
from bing import BingAPI
from yahoo import YahooAPI

def import_class(class_full_name):
    components = str(class_full_name).split('.')
    module_name = ".".join(components[:-1])
    class_name = components[-1]
    mod = __import__(module_name, fromlist=[class_name])
    return getattr(mod, class_name)

def create_api(config, api_name):
    api_fabric = import_class(api_name)
    return api_fabric.from_config(config[api_name])
