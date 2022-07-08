# Copyright 2022 aaaaaaaalesha

import os
import zipfile

from bs4 import BeautifulSoup
from prettytable import PrettyTable

import src.constants as const
from src.identifier.injector import decode_base64_id, IncorrectExtensionException
from src.ssdeep import compare as ssdeep_cmp


class NoIdentifierException(Exception):
    pass


def __parse_fields(words_: list, out_dict_: dict) -> None:
    creator_index = 0
    for i in range(len(words_)):
        out_dict_[const.FILE_NAME] += words_[i]
        if words_[i].endswith(const.VALID_EXTENSIONS):
            creator_index = i + 1
            break

    out_dict_[const.FUZZY_HASH] = words_[-1]
    out_dict_[const.MODIFIED_TIME] = words_[-2]
    out_dict_[const.CREATION_TIME] = words_[-3]
    out_dict_[const.WORKPLACE_NAME] = words_[-4]

    for i in range(creator_index, len(words_) - 4):
        out_dict_[const.CREATOR_NAME] += words_[i]


def parse_document_identifier(file: str) -> dict:
    out_dict = {
        const.FILE_NAME: '',
        const.CREATOR_NAME: '',
        const.WORKPLACE_NAME: '',
        const.CREATION_TIME: '',
        const.MODIFIED_TIME: '',
        const.FUZZY_HASH: '',
        const.IS_HASH_INTEGRITY: False
    }

    extension = os.path.splitext(file)[1]
    if extension not in const.VALID_EXTENSIONS:
        raise IncorrectExtensionException(
            f'Valid file should have extension from {const.VALID_EXTENSIONS}. Not {extension}.'
        )

    with zipfile.ZipFile(file, 'r') as zip_ref:
        soup = BeautifulSoup(zip_ref.read(const.APP), 'xml')
        description_tag = soup.find(const.DOC_DC_DESCRIPTION)

        if description_tag is not None and description_tag.string:
            words = decode_base64_id(description_tag.string).split()
            __parse_fields(words, out_dict)
        else:
            raise NoIdentifierException(f'File {file} have no identifier.')

        # Check explicit fuzzy hash existence in cp:keywords tag.
        soup = BeautifulSoup(zip_ref.read(const.CORE), 'xml')
        keywords_tag = soup.find(const.DOC_CP_KEYWORDS)

        if keywords_tag is not None:
            out_dict[const.IS_HASH_INTEGRITY] = \
                keywords_tag.string == out_dict[const.FUZZY_HASH]

    return out_dict


def match_check(s1, s2) -> str:
    return f"{const.MATCH} matches" if s1 == s2 else f"{const.MISMATCH} mismatches"


def identity_check(file1: str, file2: str) -> str:
    table = PrettyTable(
        field_names=('', 'Document 1', 'Document 2', 'Matching')
    )
    out1: dict = parse_document_identifier(file1)
    out2: dict = parse_document_identifier(file2)

    row_names = (const.FILE_NAME, const.CREATOR_NAME, const.WORKPLACE_NAME, const.CREATION_TIME,
                 const.MODIFIED_TIME, const.FUZZY_HASH, const.IS_HASH_INTEGRITY)
    for name in row_names:
        row = [name, out1[name], out2[name]]
        if name == const.FUZZY_HASH:
            row.append(f'{ssdeep_cmp(out1[name], out2[name])} %')
        else:
            row.append(match_check(out1[name], out2[name]))

        table.add_row(row)

    return str(table)
