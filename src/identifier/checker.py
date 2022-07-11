# Copyright 2022 aaaaaaaalesha

import os
import zipfile

from bs4 import BeautifulSoup
from prettytable import PrettyTable

import src.constants as const
from src.utils import decode_base64_id
from src.identifier.injector import IncorrectExtensionException
from src.ssdeep import compare as ssdeep_cmp


class NoIdentifierException(Exception):
    pass


def __parse_fields(words_: list, out_dict_: dict) -> None:
    """
    Parses all fields from words_ into out_dict_.
    :param words_: list of fields in injected identifier
    :param out_dict_: dict for stacking fields
    :return: None
    """
    creator_index = 0
    for i in range(len(words_)):
        if i != 0:
            out_dict_[const.FILE_NAME] += ' '
        out_dict_[const.FILE_NAME] += words_[i]
        if words_[i].endswith(const.VALID_EXTENSIONS):
            creator_index = i + 1
            break

    out_dict_[const.FUZZY_HASH] = words_[-1]
    out_dict_[const.MODIFIED_TIME] = words_[-2]
    out_dict_[const.CREATION_TIME] = words_[-3]
    out_dict_[const.WORKPLACE_NAME] = words_[-4]

    for i in range(creator_index, len(words_) - 4):
        if i != creator_index:
            out_dict_[const.CREATOR_NAME] += ' '
        out_dict_[const.CREATOR_NAME] += words_[i]


def __match_check(attr1, attr2) -> str:
    """
    Builds message for the right column of the matching result table.
    :param attr1: first attribute in comparison
    :param attr2: second attribute in comparison
    :return: resulted message
    """
    if all((attr1 != const.NOT_FOUND, attr2 != const.NOT_FOUND)) and attr1 == attr2:
        return const.MATCH

    return const.MISMATCH


def parse_document_identifier(file: str) -> dict:
    """
    Parse file identifier in dict of information fields.
    :param file: path to file
    :return: fields dict
    """
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
        soup = BeautifulSoup(zip_ref.read(const.CORE), 'xml')
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
            out_dict[const.IS_HASH_INTEGRITY] = keywords_tag.string == out_dict[const.FUZZY_HASH]

    return out_dict


def identity_check(file1: str, file2: str) -> str:
    """
    Builds string with table of matching files' identifiers data.
    :param file1: first file path
    :param file2: second file path
    :return: resulted sting table
    """
    table = PrettyTable(
        field_names=('', 'First Document', 'Second Document', 'Matching')
    )
    out1: dict = parse_document_identifier(file1)
    out2: dict = parse_document_identifier(file2)

    row_names = (const.FILE_NAME, const.CREATOR_NAME, const.WORKPLACE_NAME, const.CREATION_TIME,
                 const.MODIFIED_TIME, const.FUZZY_HASH, const.IS_HASH_INTEGRITY)
    for name in row_names:
        row = [name, out1[name], out2[name]]
        if name != const.FUZZY_HASH:
            row.append(__match_check(out1[name], out2[name]))
        else:
            row.append(f'{ssdeep_cmp(out1[name], out2[name])} %')

        table.add_row(row)

    return str(table)
