# Copyright 2022 aaaaaaaalesha

import csv
import os.path
from datetime import datetime
from typing import Tuple

import src.constants as const
from src.ssdeep import compare as ssdeep_cmp
from src.utils import get_file_sha3


def write_compare_results(data: Tuple[dict, dict], to_file: str, lhs: str) -> None:
    extension = os.path.splitext(lhs)[1]
    if extension in const.DOC_EXTENSIONS:
        _write_document_results(data, to_file, lhs)
    else:
        _write_image_results(data, to_file, lhs)


def _write_document_results(data: Tuple[dict, dict], to_file: str, lhs: str) -> None:
    dict1, dict2 = data[0], data[1]
    current_dt = f"{datetime.now():%d.%m.%Y %H:%M:%S}"
    sha3_hash = get_file_sha3(lhs)
    fhash1, fhash2 = dict1[const.FUZZY_HASH], dict2[const.FUZZY_HASH]

    new_row = [current_dt] + [val for val in dict1.values()] + [sha3_hash] + \
              [val for val in dict2.values()] + [f'{ssdeep_cmp(fhash1, fhash2)} %']

    __write_row(to_file, dict1, dict2, new_row)


def _write_image_results(data: Tuple[dict, dict], to_file: str, lhs: str) -> None:
    dict1, dict2 = data[0], data[1]
    current_dt = f"{datetime.now():%d.%m.%Y %H:%M:%S}"
    sha3_hash = get_file_sha3(lhs)

    basename, extension = os.path.splitext(to_file)
    to_file = f'{basename} (img){extension}'

    hash_string_builder = [f'{100 - (dict1[name] - dict2[name])}' for name in dict1.keys() if name.endswith('hash')]

    new_row = [current_dt] + [str(fld) for fld in dict1.values()] + [sha3_hash] + \
              [str(fld) for fld in dict2.values()] + [' % '.join(hash_string_builder)]

    __write_row(to_file, dict1, dict2, new_row)


def __write_row(to_file: str, dict1: dict, dict2: dict, new_row: list) -> None:
    if not os.path.exists(to_file):
        with open(to_file, 'w', encoding='utf-8') as file:
            field_names = ['DateTime'] + [f'{fld} 1' for fld in dict1.keys()] + ['SHA3-hash'] + \
                          [f'{fld} 2' for fld in dict2.keys()] + ['Matching']
            writer = csv.writer(file)
            writer.writerow(field_names)
            writer.writerow(new_row)
    elif os.path.splitext(to_file)[1] == '.csv':
        with open(to_file, 'a', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(new_row)
