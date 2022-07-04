# Copyright 2022 aaaaaaaalesha
import base64
import os
import subprocess
import zipfile
import shutil

from bs4 import BeautifulSoup

import src.constants as const
import src.ssdeep as ssdeep


class IncorrectExtensionException(Exception):
    pass


class IdentifierInjector:
    """Class implements generating identifier for .docx/.xlsx files and its injection."""

    def __init__(self, path: str):
        self.__path = path

        extension = os.path.splitext(path)[1]
        if extension not in const.VALID_EXTENSIONS:
            raise IncorrectExtensionException(
                f'Valid file should have extension from {const.VALID_EXTENSIONS}. Not {extension}.'
            )
        self.__path = path

        # Saving document name.
        self.__file_name = os.path.basename(path)

        with zipfile.ZipFile(path, 'r') as zip_ref:
            soup = BeautifulSoup(zip_ref.read(const.CORE), 'xml')

            # Saving name of creator.
            self.__creator_name = soup.find(const.DOC_CREATOR_TAG).string

            # TODO: Saving automated workplace name.
            # how to find it?

            # Saving creation time.
            self.__creation_time = soup.find(const.DOC_DT_CREATED).string

        if not self.__is_injected():
            self.__fuzzy_hash = ssdeep.hash_from_file(path)

    def __is_injected(self) -> bool:
        """
        Method checks is identifier already injected.
        :return: True if identifier is already injected in document, False – otherwise.
        """
        with zipfile.ZipFile(self.__path, 'r') as zip_ref:
            soup = BeautifulSoup(zip_ref.read(const.APP), 'xml')
            company_tag = soup.find('Company')

            if company_tag is not None and company_tag.string:
                positions = decode_base64_id(company_tag.string).rsplit()
                self.__fuzzy_hash = positions[-1]
                return True

        return False

    def __write_identifier(self) -> None:
        """
        Writes identifier in docProps/app.xml in tag <Company> like base64-string.
        :return: None
        """
        soup: BeautifulSoup = BeautifulSoup()

        with open(f'{const.TEMP_DIR}/{const.APP}', 'r', encoding='utf-8') as app_xml:
            soup = BeautifulSoup(app_xml.read(), 'xml')

        company_tag = soup.find('Company')
        text_id = f'{self.__file_name} {self.__creator_name} {self.__creation_time} {self.__fuzzy_hash}'

        # Inject base64 identifier in company tag if it exists.
        if company_tag is not None:
            company_tag.string = encode_base64_id(text_id)
        else:
            soup.find("Properties").append(
                BeautifulSoup(f"<Company>{encode_base64_id(text_id)}</Company>", 'xml')
            )

        with open(f'{const.TEMP_DIR}/{const.APP}', 'w', encoding='utf-8') as app_xml:
            app_xml.write(str(soup))

    def __set_explicit_fuzzy_hash(self) -> None:
        """
        Setting fuzzy hash explicitly in docProps/core.xml in tag <cp:keywords>.
        :return: None
        """
        soup: BeautifulSoup = BeautifulSoup()

        with open(f'{const.TEMP_DIR}/{const.CORE}', 'r', encoding='utf-8') as core_xml:
            soup = BeautifulSoup(core_xml.read(), 'xml')

            keywords_tag = soup.find(const.DOC_CP_KEYWORDS)

            # Paste fuzzy hash in cp:keywords tag if it exists.
            if keywords_tag is not None:
                keywords_tag.string = self.__fuzzy_hash
            else:
                soup.find("cp:coreProperties").append(
                    BeautifulSoup(f"<cp:keywords>{self.__fuzzy_hash}</cp:keywords>", 'xml')
                )

        with open(f'{const.TEMP_DIR}/{const.CORE}', 'w', encoding='utf-8') as core_xml:
            core_xml.write(str(soup))

    def inject_identifier(self, out_folder: str) -> None:
        """
        Injects base64-string representation of identifier into document.

        :param out_folder: path for writing documents with injected
        :return: None.
        """
        if not os.path.exists(self.__path):
            raise FileNotFoundError(f'File {self.__file_name} is no longer available at {self.__path}.')

        if os.path.exists(out_folder) and not os.path.isdir(out_folder):
            raise NotADirectoryError(f'Path "{out_folder}" should be accessible directory to write injected documents.')

        with zipfile.ZipFile(self.__path, 'r') as zip_ref:
            zip_ref.extractall(const.TEMP_DIR)

        self.__write_identifier()

        self.__set_explicit_fuzzy_hash()

        subprocess.run(
            f'cd {const.TEMP_DIR} && zip -r {self.__file_name} .'.split(),
            shell=True,
        )

        if os.path.exists(f'{out_folder}/{self.__file_name}'):
            os.remove(f'{out_folder}/{self.__file_name}')

        shutil.move(f'{const.TEMP_DIR}/{self.__file_name}', out_folder)
        shutil.rmtree(const.TEMP_DIR)


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
    base64_bytes = base64.b64decode(
        text.encode('utf-8')
    )

    return base64_bytes.decode('utf-8')
