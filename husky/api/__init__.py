# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

# Import Google APIs
from husky.api.google import CseAPI
from husky.api.google import CseError

API_ID_2_API = {
    "api.GoogleCSE": CseAPI,
}


def create_api(api_config):
    assert("id" in api_config)
    api_fabric = API_ID_2_API.get(api_config["id"])
    if api_fabric is None:
        raise ValueError("API ID has value or not implemented (%s)" % api_config["id"])
    return api_fabric.from_config(api_config)
