# Copyright 2022 aaaaaaaalesha
import os
import zipfile
from typing import Tuple

from bs4 import BeautifulSoup
from prettytable import PrettyTable

import src.constants as const
from src.identifier.injector import decode_base64_id, IncorrectExtensionException
from src.ssdeep import compare as ssdeep_cmp


class NoIdentifierException(Exception):
    pass


def parse_document_identifier(file: str) -> Tuple[str, str, str, str, bool]:
    file_name, creator_name, creation_time, fuzzy_hash = '', '', '', ''

    extension = os.path.splitext(file)[1]
    if extension not in const.VALID_EXTENSIONS:
        raise IncorrectExtensionException(
            f'Valid file should have extension from {const.VALID_EXTENSIONS}. Not {extension}.'
        )

    with zipfile.ZipFile(file, 'r') as zip_ref:
        soup = BeautifulSoup(zip_ref.read(const.APP), 'xml')
        company_tag = soup.find('Company')

        if company_tag is not None and company_tag.string:
            words = decode_base64_id(company_tag.string).split()

            creator_index = 0
            for i in range(len(words)):
                file_name += words[i]
                if words[i].endswith(const.VALID_EXTENSIONS):
                    creator_index = i + 1
                    break

            fuzzy_hash = words[-1]
            creation_time = words[-2]

            for i in range(creator_index, len(words) - 2):
                creator_name += words[i]
        else:
            raise NoIdentifierException(f'File {file} have no identifier.')

        # Check explicit fuzzy hash existence in cp:keywords tag.
        soup = BeautifulSoup(zip_ref.read(const.CORE), 'xml')
        keywords_tag = soup.find(const.DOC_CP_KEYWORDS)

        is_hash_explicitly_exists = False
        if keywords_tag is not None:
            is_hash_explicitly_exists = keywords_tag.string == fuzzy_hash

    return file_name, creator_name, creation_time, fuzzy_hash, is_hash_explicitly_exists


def match_check(s1, s2) -> str:
    return f"{const.MATCH} matches" if s1 == s2 else f"{const.MISMATCH} mismatches"


def identity_check(file1: str, file2: str) -> str:
    table = PrettyTable(
        field_names=('', 'Document 1', 'Document 2', 'Matching')
    )
    res1 = parse_document_identifier(file1)
    res2 = parse_document_identifier(file2)

    table.add_rows((
        ('Filename', res1[0], res2[0], match_check(res1[0], res2[0])),
        ('Creator name', res1[1], res2[1], match_check(res1[1], res2[1])),
        ('Creation time', res1[2], res2[2], match_check(res1[2], res2[2])),
        ('Fuzzy hash', res1[3], res2[3], f'{ssdeep_cmp(res1[3], res2[3])} %'),
        ('Hash integrity', res1[4], res2[4], match_check(res1[4], res2[4])),
    ))

    return str(table)
