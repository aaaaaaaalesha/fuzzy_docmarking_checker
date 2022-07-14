# Copyright 2022 aaaaaaaalesha

import base64
import os
import zipfile

from bs4 import BeautifulSoup


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


def zip_path_to_file(dir_path: str, file_path: str) -> None:
    """
    Zips all files and subdirectories from directory path in file_path
    :param dir_path: path to directory for zipping
    :param file_path: out file path for zipping
    :return: None
    """
    if os.path.exists(file_path):
        os.remove(file_path)

    if not os.path.isdir(dir_path):
        raise NotADirectoryError(f'{dir_path} is not directory.')

    with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                filename = os.path.join(root, file)
                relpath = os.path.relpath(os.path.join(root, file), dir_path)
                zipf.write(filename, relpath)


def extract_xml_tags(path: str, out_list: list, tag_name: str, attrs=False) -> None:
    """
    Finds all tags in xml file and appends its str representation content to out_list.
    :param path: path to xml file
    :param out_list: list for tags content extracting
    :param tag_name: name of tags we are searching for
    :param attrs: if True adds full tag, otherwise – only string content inside
    :return: None
    """
    with open(path, encoding='utf-8') as file:
        soup = BeautifulSoup(file.read(), 'xml')
        for tag in soup.find_all(tag_name):
            if attrs:
                out_list.append(str(tag))
                continue

            if tag.string is not None:
                out_list.append(tag.string)
