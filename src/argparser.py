# Copyright 2022 aaaaaaaalesha

import sys
import os.path

import argparse

from src.identifier import injector, checker
from constants import VALID_EXTENSIONS


def injection(path_to_file: str, out_dir: str) -> None:
    id_ = injector.IdentifierInjector(path_to_file)
    id_.inject_identifier(out_dir)
    print(f"Identifier was injected successfully in document "
          f"{os.path.join(out_dir, os.path.basename(path_to_file))}")


def launch():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inject', type=str, nargs='+',
                        help='Inject identifier in document(s). If the passed path is a directory, '
                             'the identifier will be injected in all files with the desired extension.')
    parser.add_argument('-o', '--output', type=str, nargs=1,
                        help='Destination folder for saving injected document(s)')
    parser.add_argument('-c', '--compare', type=str, nargs=2,
                        help='Compare two documents by their identifiers.')

    args = parser.parse_args()
    if args.inject:
        if not args.output:
            parser.error("Named argument -o (--output) required.")
            sys.exit(1)

        for path in args.inject:
            if not os.path.exists(path):
                print(f"Path {path} does not exist")
                continue

            if not os.path.isdir(path):
                injection(path, *args.output)
                continue

            for file in os.listdir(path):
                path_to_file = os.path.join(path, file)
                extension = os.path.splitext(path_to_file)[1]
                if not os.path.isdir(path_to_file) and extension in VALID_EXTENSIONS:
                    injection(path_to_file, *args.output)

        print("Completed")
    elif args.compare:
        print(checker.identity_check(*args.compare))
    else:
        parser.print_help()
