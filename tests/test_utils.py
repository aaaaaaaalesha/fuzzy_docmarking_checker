# Copyright 2022 aaaaaaaalesha

import os

import src.utils as utils


def test_base64_coding():
    for n in range(50):
        test_str = str(os.urandom(n))
        assert test_str == utils.decode_base64_id(
            utils.encode_base64_id(test_str)
        )
