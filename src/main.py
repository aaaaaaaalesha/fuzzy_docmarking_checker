# Copyright 2022 aaaaaaaalesha

from identifier import injector, checker

if __name__ == '__main__':
    path1 = "../rpz1.docx"
    path2 = "../rpz2.docx"

    id_1 = injector.IdentifierInjector(path1)
    id_2 = injector.IdentifierInjector(path2)

    id_1.inject_identifier('../out/')
    id_2.inject_identifier('../out/')

    print(checker.identity_check('../out/rpz1.docx', '../out/rpz2.docx'))
