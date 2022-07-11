# Copyright 2022 aaaaaaaalesha

import base64
import os


def encode_base64_id(text: str) -> str:
    """
    Encodes identifier to base64-string.
    :param text: string;
    :return: base64 string representation
    """
    base64_bytes = base64.b64encode(
        text.encode('utf-8')
    )

    return base64_bytes.decode('utf-8')


def decode_base64_id(text: str) -> str:
    """
    Decodes base64-string to representable string.
    :param text: base64-string;
    :return: decoded representable string
    """
    base64_bytes = base64.b64decode(text.encode('utf-8'))

    return base64_bytes.decode('utf-8')


def get_files_list(path: str) -> list:
    """
    Collects all files names in path
    :param path: path for parsing files
    :return: list of files' paths
    """
    out_list = []
    for f in os.listdir(path):
        p = os.path.join(path, f)
        if os.path.isfile(p):
            out_list.append(p)

    return out_list
