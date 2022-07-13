# Copyright 2022 aaaaaaaalesha

import os
import zipfile

import imagehash
from bs4 import BeautifulSoup
from prettytable import PrettyTable

import src.constants as const
from src.utils import decode_base64_id
from src.identifier.injector import IncorrectExtensionException
from src.ssdeep import compare as ssdeep_cmp


class NoIdentifierException(Exception):
    pass


def identity_check(file1: str, file2: str) -> str:
    """
    Builds string with table of matching files' identifiers data.
    :param file1: first file path
    :param file2: second file path
    :return: resulted sting table
    """
    table = PrettyTable(
        field_names=('', 'First File', 'Second File', 'Matching')
    )

    if not _comparable(file1, file2):
        raise IncorrectExtensionException('Files to compare have incomparable extensions')

    out1: dict = parse_file_identifier(file1)
    out2: dict = parse_file_identifier(file2)

    row_names = tuple(out1.keys())

    for name in row_names:
        row = [name, out1[name], out2[name]]
        if not name.endswith('hash'):
            row.append(__match_check(out1[name], out2[name]))
        else:
            if isinstance(out1[name], imagehash.ImageHash):
                row.append(f'{100 - (out1[name] - out2[name])} %')
            else:
                row.append(f'{ssdeep_cmp(out1[name], out2[name])} %')

        table.add_row(row)

    return str(table)


def parse_file_identifier(file: str) -> dict:
    """
    Parses file identifier in dict of information fields.
    :param file:path to file
    :return:
    """
    extension = os.path.splitext(file)[1]
    if extension in const.DOC_EXTENSIONS:
        return _parse_document_identifier(file)
    elif extension in const.IMG_EXTENSIONS:
        return _parse_image_identifier(file)
    else:
        raise IncorrectExtensionException(
            f'Valid file should have extension like {", ".join(const.VALID_EXTENSIONS)}. Not {extension}.'
        )


def _comparable(file1_: str, file2_: str) -> bool:
    """
    Checks are files comparable or not.
    :param file1_: path to first file
    :param file2_: path to second file
    :return: True if files are comparable, False – otherwise
    """
    ext1 = os.path.splitext(file1_)[1]
    ext2 = os.path.splitext(file2_)[1]

    if ext1 in const.DOC_EXTENSIONS and ext2 in const.DOC_EXTENSIONS:
        return True
    elif ext1 in const.IMG_EXTENSIONS and ext2 in const.IMG_EXTENSIONS:
        return True

    return False


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


def _parse_document_identifier(doc_file: str) -> dict:
    """
    Parses document identifier in dict of information fields.
    :param doc_file: path to doc_file
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

    with zipfile.ZipFile(doc_file, 'r') as zip_ref:
        soup = BeautifulSoup(zip_ref.read(const.CORE), 'xml')
        description_tag = soup.find(const.DOC_DC_DESCRIPTION)

        if description_tag is not None and description_tag.string:
            words = decode_base64_id(description_tag.string).split()
            __get_document_fields(words, out_dict)
        else:
            raise NoIdentifierException(f'File {doc_file} has no identifier.')

        # Check explicit fuzzy hash existence in cp:keywords tag.
        soup = BeautifulSoup(zip_ref.read(const.CORE), 'xml')
        keywords_tag = soup.find(const.DOC_CP_KEYWORDS)

        if keywords_tag is not None:
            out_dict[const.IS_HASH_INTEGRITY] = keywords_tag.string == out_dict[const.FUZZY_HASH]

    return out_dict


def _parse_image_identifier(img_file: str) -> dict:
    """
    Parse image identifier in dict of information fields.
    :param img_file: path to img_file
    :return: fields dict
    """
    filename = os.path.basename(os.path.splitext(img_file)[0])
    # Take all instead defaulthash.
    fields = filename.split('_', maxsplit=5)

    from_file = decode_base64_id(fields[0])
    avghash, dhash, phash, = map(imagehash.hex_to_hash, fields[1:4])
    colorhash = imagehash.hex_to_flathash(fields[4], 2)

    return dict(zip(const.IMG_FIELDS, (from_file, avghash, dhash, phash, colorhash)))


def __get_document_fields(words_: list, out_dict_: dict) -> None:
    """
    Puts all fields from words_ into out_dict_.
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
