# Copyright 2022 aaaaaaaalesha

import csv
import os.path
from datetime import datetime
from typing import Tuple

import src.constants as const
from src.ssdeep import compare as ssdeep_cmp
from src.utils import get_file_sha3


def write_compare_results(data: Tuple[dict, dict], to_file: str, lhs: str) -> None:
    current_dt = f"{datetime.now():%d.%m.%Y %H:%M:%S}"
    sha3_hash = get_file_sha3(lhs)

    fhash1, fhash2 = data[0][const.FUZZY_HASH], data[1][const.FUZZY_HASH]
    new_row = (current_dt, data[0][const.FILE_NAME], fhash1, sha3_hash,
               data[1][const.FILE_NAME], fhash2, f'{ssdeep_cmp(fhash1, fhash2)} %')

    if not os.path.exists(to_file):
        with open(to_file, 'w') as file:
            field_names = ('DateTime', 'Filename1', 'Fuzzy-hash1', 'SHA3-hash', 'Filename2', 'Fuzzy-hash2', 'Matching')
            writer = csv.writer(file)
            writer.writerow(field_names)
            writer.writerow(new_row)
    elif os.path.splitext(to_file)[1] == '.csv':
        with open(to_file, 'a') as file:
            writer = csv.writer(file)
            writer.writerow(new_row)
