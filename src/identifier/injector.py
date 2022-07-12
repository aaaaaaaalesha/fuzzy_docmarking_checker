# Copyright 2022 aaaaaaaalesha

import os
import socket
import subprocess
import zipfile
import shutil

from bs4 import BeautifulSoup

import src.constants as const
import src.ssdeep as ssdeep
import src.utils as utils


class IncorrectExtensionException(Exception):
    pass


class IdentifierInjector:
    """Class implements generating identifier for .docx/.xlsx files and its injection."""

    def __init__(self, path: str):
        self.__path = path

        self.__extension = os.path.splitext(path)[1]
        if self.__extension not in const.VALID_EXTENSIONS:
            raise IncorrectExtensionException(
                f'Valid file should have extension from {const.VALID_EXTENSIONS}. Not {self.__extension}.'
            )
        self.__path = path

        # Saving document name.
        self.__file_name = os.path.basename(path)

        with zipfile.ZipFile(path, 'r') as zip_ref:
            soup = BeautifulSoup(zip_ref.read(const.CORE), 'xml')

        # Saving name of creator.
        tag = soup.find(const.DOC_CREATOR_TAG)
        self.__creator_name = tag.string if tag is not None and tag.string else const.NOT_FOUND

        # Saving name of workplace.
        self.__workplace_name = socket.gethostname()

        # Saving creation time.
        tag = soup.find(const.DOC_DT_CREATED)
        self.__creation_time = tag.string if tag is not None and tag.string else const.NOT_FOUND

        # Saving last modification time.
        tag = soup.find(const.DOC_DT_MODIFIED)
        self.__modified_time = tag.string if tag is not None and tag.string else const.NOT_FOUND

        if not self.__is_injected():
            self.__fuzzy_hash = self.__get_fuzzy_hash()

    def __is_injected(self) -> bool:

        """
        Method checks is identifier already injected.
        :return: True if identifier is already injected in document, False – otherwise.
        """
        with zipfile.ZipFile(self.__path, 'r') as zip_ref:
            soup = BeautifulSoup(zip_ref.read(const.CORE), 'xml')
            description_tag = soup.find(const.DOC_DC_DESCRIPTION)

            if description_tag is not None and description_tag.string:
                try:
                    positions = utils.decode_base64_id(description_tag.string).rsplit()
                except UnicodeDecodeError:
                    return False
                self.__fuzzy_hash = positions[-1]
                return True

        return False

    def __get_fuzzy_hash(self) -> str:
        """
        Returns fuzzy hash, of .docx/.xlsx file.
        :return: str-fuzzy hash.
        """
        string_builder = list()
        with zipfile.ZipFile(self.__path, 'r') as zip_ref:
            zip_ref.extractall(const.TEMP_DIR)

        source_dir = const.TEMP_DIR
        if self.__extension == '.docx':
            source_dir += '/word'
        else:  # if '.xlsx'
            source_dir += '/xl'

        # Collecting all files in a directory
        files_list = utils.get_files_list(source_dir)
        if self.__extension == '.xlsx':
            files_list += utils.get_files_list(f'{source_dir}/worksheets')
        for file in files_list:
            with open(file, encoding='utf-8') as f:
                string_builder.append(f.read())

        shutil.rmtree(const.TEMP_DIR)

        return ssdeep.hash(''.join(string_builder))

    def __write_identifier(self) -> None:

        """
        Writes identifier in docProps/core.xml in tag <dc:description> like base64-string.
        :return: None
        """

        soup: BeautifulSoup = BeautifulSoup()

        with open(f'{const.TEMP_DIR}/{const.CORE}', 'r', encoding='utf-8') as core_xml:
            soup = BeautifulSoup(core_xml.read(), 'xml')

        description_tag = soup.find(const.DOC_DC_DESCRIPTION)
        text_id = f'{self.__file_name} {self.__creator_name} {self.__workplace_name} ' \
                  f'{self.__creation_time} {self.__modified_time} {self.__fuzzy_hash}'

        # Inject base64 identifier in company tag if it exists.
        if description_tag is not None:
            description_tag.string = utils.encode_base64_id(text_id)
        else:
            soup.find(const.DOC_CORE_PROPERTIES).append(
                BeautifulSoup(
                    f'<{const.DOC_DC_DESCRIPTION}>{utils.encode_base64_id(text_id)}</{const.DOC_DC_DESCRIPTION}>',
                    'xml',
                ))

            # Tag needs correction, because of wrong parsing of bs4.
            tag = soup.find('description')
            if tag is not None:
                tag.name = const.DOC_DC_DESCRIPTION

        with open(f'{const.TEMP_DIR}/{const.CORE}', 'w', encoding='utf-8') as core_xml:
            core_xml.write(str(soup))

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
                soup.find(const.DOC_CORE_PROPERTIES).append(
                    BeautifulSoup(f"<{const.DOC_CP_KEYWORDS}>{self.__fuzzy_hash}</{const.DOC_CP_KEYWORDS}>", 'xml')
                )

                # Tag needs correction, because of wrong parsing of bs4.
                tag = soup.find('keywords')
                if tag is not None:
                    tag.name = const.DOC_CP_KEYWORDS

        with open(f'{const.TEMP_DIR}/{const.CORE}', 'w', encoding='utf-8') as core_xml:
            core_xml.write(str(soup))

    def inject_identifier(self, out_folder: str) -> None:

        """
        Injects base64-string representation of identifier into document.

        :param: out_folder: path for writing documents with injected
        :return: None.
        """

        if not os.path.exists(self.__path):
            raise FileNotFoundError(f'File {self.__file_name} is no longer available at {self.__path}.')

        if not os.path.exists(out_folder):
            os.makedirs(out_folder)

        if not os.path.isdir(out_folder):
            raise NotADirectoryError(f'Path "{out_folder}" should be accessible directory to write injected documents.')

        with zipfile.ZipFile(self.__path, 'r') as zip_ref:
            zip_ref.extractall(const.TEMP_DIR)

        self.__set_explicit_fuzzy_hash()

        self.__write_identifier()

        utils.zip_path_to_file(f'{const.TEMP_DIR}', f'{out_folder}/{self.__file_name}')

        shutil.rmtree(const.TEMP_DIR)
