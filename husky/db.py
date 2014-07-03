# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import plyvel


def MB(number):
    return 1024 * 1024 * number


def create(db_path):
    return plyvel.DB(db_path,
                     write_buffer_size=MB(1024),
                     block_size=MB(512),
                     bloom_filter_bits=8,
                     create_if_missing=True,
                     error_if_exists=True)


def open(path):
    return plyvel.DB(path, create_if_missing=False)