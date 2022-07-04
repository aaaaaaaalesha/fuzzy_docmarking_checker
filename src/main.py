# Copyright 2022 aaaaaaaalesha
import base64
import os

from identifier import id

if __name__ == '__main__':
    path = "B:\\github\\fuzzy_docmarking_checker\\test.docx"

    id_ = id.Identifier(path)

    id_.inject_identifier('../out/')
