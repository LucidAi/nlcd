#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import sys
import logging
import argparse


class FenrirWorker(object):

    def __init__(self):
        pass


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-v",
                           "--verbosity-level",
                           type=int,
                           default=1,
                           choices=(0, 1, 2))
    argparser.add_argument("-iu",
                           "--input-url",
                           type=str,
                           default=None)
    argparser.add_argument("-iu",
                           "--input-url",
                           type=str,
                           default=None)

    arguments = argparser.parse_args()

    if arguments.verbosity_level == 1:
        logging.basicConfig(level=logging.INFO)
    if arguments.verbosity_level == 2:
        logging.basicConfig(level=logging.DEBUG)
