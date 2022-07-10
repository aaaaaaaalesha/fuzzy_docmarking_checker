# Copyright 2022 aaaaaaaalesha

from identifier import injector, checker

import argparse

parser = argparse.ArgumentParser()

if __name__ == '__main__':
    id_1 = injector.IdentifierInjector("../rpz1.xlsx")
    id_2 = injector.IdentifierInjector("../rpz2.xlsx")

    id_1.inject_identifier('../out/')
    id_2.inject_identifier('../out/')

    print(checker.identity_check('../out/rpz1.xlsx', '../out/rpz2.xlsx'))
