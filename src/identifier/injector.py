# Copyright 2022 aaaaaaaalesha

import os
import socket
import zipfile
import shutil

from bs4 import BeautifulSoup
from imagehash import average_hash, dhash, phash, colorhash
from tempfile import mkdtemp
from PIL import Image

import src.constants as const
import src.ssdeep as ssdeep
import src.utils as utils


class InvalidExtensionException(Exception):
    pass


class IdentifierInjector:
    """
    Class implements generating identifier for files and its injection.
    Supported file extensions:
    - .docx, .xlsx – documents;
    - .jpg, .png, .bmp – images.
    """

    def __init__(self, path: str):
        self.__path = path

        self.__extension = os.path.splitext(path)[1]
        if self.__extension not in const.VALID_EXTENSIONS:
            raise InvalidExtensionException(
                f'Valid file should have extension like {", ".join(const.VALID_EXTENSIONS)}. Not {self.__extension}.'
            )
        self.__path = path

        # Saving document name.
        self.__file_name = os.path.basename(path)

        if self.__extension in const.DOC_EXTENSIONS:
            self.__collect_document_fields()
        else:
            self.__collect_img_fields()

    def inject_identifier(self, out_folder: str) -> None:
        """
        Injects identifier in file and puts it to out_folder directory.
        :param: out_folder: destination directory path for injected file
        :return: None.
        """
        if not os.path.exists(self.__path):
            raise FileNotFoundError(f'File {self.__file_name} is no longer available at {self.__path}.')

        if not os.path.exists(out_folder):
            os.makedirs(out_folder)

        if not os.path.isdir(out_folder):
            raise NotADirectoryError(f'Path "{out_folder}" should be accessible directory to write injected documents.')

        if self.__extension in const.DOC_EXTENSIONS:
            self.__document_injection(out_folder)
        else:
            self.__image_injection(out_folder)

    def _is_injected(self) -> bool:
        """
        Method checks is identifier already injected in document.
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

                return True

        return False

    def __collect_document_fields(self) -> None:
        """
        Collects all needed fields for document.
        :return: None
        """
        with zipfile.ZipFile(self.__path, 'r') as zip_ref:
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

        self.__fuzzy_hash = self.__get_fuzzy_hash()

    def __collect_img_fields(self) -> None:
        """
        Collects all needed fields for image.
        :return: None
        """
        with Image.open(self.__path) as img:
            self.__defaulthash = hash(self.__path)
            self.__avghash = str(average_hash(img))
            self.__dhash = str(dhash(img))
            self.__phash = str(phash(img))
            self.__colorhash = str(colorhash(img))

    def __get_fuzzy_hash(self) -> str:
        """
        Returns fuzzy hash, of .docx/.xlsx file.
        :return: str-fuzzy hash.
        """
        string_builder = list()
        tempdir = mkdtemp()
        with zipfile.ZipFile(self.__path, 'r') as zip_ref:
            zip_ref.extractall(tempdir)

        source_dir = tempdir
        if self.__extension == '.docx':
            source_dir += f'{os.sep}word'
            self.__collect_word_content(source_dir, string_builder)
        else:  # if '.xlsx'
            source_dir += f'{os.sep}xl{os.sep}worksheets'
            self.__collect_excel_content(source_dir, string_builder)

        shutil.rmtree(tempdir)

        return ssdeep.hash(''.join(string_builder))

    @staticmethod
    def __collect_word_content(source_dir_: str, string_builder_: list) -> None:
        """
        Collects all valuable content from word document.
        :param source_dir_: source directory inside unzipped word document
        :param string_builder_: list for collecting word content
        :return:
        """
        existing_files = utils.get_files_list(source_dir_)
        existing_files.sort()

        for file in existing_files:
            basename = os.path.basename(file)
            if basename == 'document.xml' or basename.startswith(('footer', 'header')):
                utils.extract_xml_tags(file, string_builder_, 'w:t')

    @staticmethod
    def __collect_excel_content(source_dir_: str, string_builder_: list) -> None:
        """
        Collects all valuable content from excel document.
        :param source_dir_: source directory inside unzipped excel document
        :param string_builder_: list for collecting excel content
        :return: None
        """
        existing_files = utils.get_files_list(source_dir_)

        for file in existing_files:
            utils.extract_xml_tags(file, string_builder_, 'sheetData', attrs=True)

    def __write_identifier(self, tempdir_path: str) -> None:

        """
        Writes identifier in docProps/core.xml in tag <dc:description> like base64-string.
        :param tempdir_path: path to temporary directory for working with external of .docx/.xlsx file
        :return: None
        """
        soup: BeautifulSoup = BeautifulSoup()

        with open(f'{tempdir_path}{os.sep}{const.CORE}', 'r', encoding='utf-8') as core_xml:
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

        with open(f'{tempdir_path}{os.sep}{const.CORE}', 'w', encoding='utf-8') as core_xml:
            core_xml.write(str(soup))

    def __set_explicit_fuzzy_hash(self, tempdir_path: str) -> None:

        """
        Setting fuzzy hash explicitly in docProps/core.xml in tag <cp:keywords>.
        :param tempdir_path: path to temporary directory for working with external of .docx/.xlsx file
        :return: None
        """

        soup: BeautifulSoup = BeautifulSoup()
        core_path = f'{tempdir_path}{os.sep}{const.CORE}'

        with open(core_path, 'r', encoding='utf-8') as core_xml:
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

        with open(core_path, 'w', encoding='utf-8') as core_xml:
            core_xml.write(str(soup))

    def __document_injection(self, out: str) -> None:
        """
        Injects base64-string representation of identifier in document.
        :param out:  path for writing documents with injected id
        :return: None
        """
        tempdir = mkdtemp()
        with zipfile.ZipFile(self.__path, 'r') as zip_ref:
            zip_ref.extractall(tempdir)

        self.__set_explicit_fuzzy_hash(tempdir)

        self.__write_identifier(tempdir)

        utils.zip_path_to_file(tempdir, f'{out}{os.sep}{self.__file_name}')

        shutil.rmtree(tempdir)

    def __image_injection(self, out: str) -> None:
        """
        Injects of identifier in the basename of image.
        :param out: path for writing documents with injected id
        :return: None
        """
        id_text = f"{utils.encode_base64_id(self.__file_name)}_{self.__avghash}_{self.__dhash}_{self.__phash}_" \
                  f"{self.__colorhash}{self.__extension}"
        shutil.copy2(self.__path, out)

        new_path_name = os.path.join(out, id_text)
        if os.path.exists(new_path_name):
            os.remove(new_path_name)

        os.rename(
            os.path.join(out, self.__file_name),
            os.path.join(out, id_text)
        )
