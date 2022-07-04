# Copyright 2022 aaaaaaaalesha
import base64
import os
import subprocess
import sys
import zipfile
import shutil

from bs4 import BeautifulSoup

import src.constants as const
import src.ssdeep as ssdeep


class IncorrectExtension(Exception):
    pass


class Identifier:
    """Class implements generating identifier for .docx/.xlsx files."""

    def __init__(self, path: str):
        self.__path = path

        extension = os.path.splitext(path)[1]
        if extension not in const.VALID_EXTENSIONS:
            raise IncorrectExtension(
                f'Valid file should have extension from {const.VALID_EXTENSIONS}. Not {extension}.'
            )
        self.__path = path

        # Saving document name.
        self.__filename = os.path.basename(path)

        with zipfile.ZipFile(path, 'r') as zip_ref:
            soup = BeautifulSoup(zip_ref.read(const.CORE), 'xml')

            # Saving name of creator.
            self.__creator_name = soup.find(const.DOC_CREATOR_TAG).string

            # TODO: Saving automated workplace name.
            # how to find it?

            # Saving creation time.
            self.__creation_time = soup.find(const.DOC_DT_CREATED).string

        self.__fuzzy_hash = ssdeep.hash_from_file(path)

    def __str__(self):
        return self.__encode_base64_id()

    def __encode_base64_id(self) -> str:
        """
        Encodes identifier to base64-string.

        :return: base64 string representation
        """
        string_id_ = f'{self.__creator_name} {self.__filename} {self.__creation_time} {self.__fuzzy_hash}'
        base64_bytes = base64.b64encode(
            string_id_.encode('utf-8')
        )

        return base64_bytes.decode('utf-8')

    def inject_identifier(self, out_folder: str) -> None:
        """
        Injects base64-string representation of identifier into document.

        :param out_folder: path for writing documents with injected
        :return: None.
        """
        if not os.path.exists(self.__path):
            raise FileNotFoundError(f'File {self.__filename} is no longer available at {self.__path}.')

        if os.path.exists(out_folder) and not os.path.isdir(out_folder):
            raise NotADirectoryError(f'Path "{out_folder}" should be accessible directory to write injected documents.')

        soup = BeautifulSoup()
        with zipfile.ZipFile(self.__path, 'r') as zip_ref:
            zip_ref.extractall(const.TEMP_DIR)

            soup = BeautifulSoup(zip_ref.read(const.APP), 'xml')
            company_tag = soup.find('Company')

            if company_tag is not None:
                company_tag.string = self.__encode_base64_id()
            else:
                soup.find("Properties").append(
                    BeautifulSoup(f"<Company>{self.__encode_base64_id()}</Company>", 'xml')
                )

        with open(f'{const.TEMP_DIR}/{const.APP}', 'w') as app_xml:
            app_xml.write(str(soup))

        subprocess.run(
            f'cd {const.TEMP_DIR} && zip -r {self.__filename} .'.split(),
            shell=True,
        )

        if os.path.exists(f'{out_folder}/{self.__filename}'):
            os.remove(f'{out_folder}/{self.__filename}')

        shutil.move(f'{const.TEMP_DIR}/{self.__filename}', out_folder)
        shutil.rmtree(const.TEMP_DIR)
