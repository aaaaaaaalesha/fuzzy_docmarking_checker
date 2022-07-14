# Copyright 2022 aaaaaaaalesha

import sys
import os.path

import argparse

from src.identifier import injector, checker
from constants import VALID_EXTENSIONS


def injection(path_to_file: str, out_dir: str) -> None:
    id_ = injector.IdentifierInjector(path_to_file)
    id_.inject_identifier(out_dir)
    print(f"Identifier was injected successfully in file {os.path.basename(path_to_file)} "
          f"and moved in out directory {os.path.abspath(out_dir)}")


def launch():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inject', type=str, nargs='+',
                        help='Inject identifier in document(s). If the passed path is a directory, '
                             'the identifier will be injected in all files with the desired extension.')
    parser.add_argument('-o', '--output', type=str, nargs=1,
                        help='Destination folder for saving injected document(s)')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Collects file for injection in folder recursively.')
    parser.add_argument('-c', '--compare', type=str, nargs='+',
                        help='Compare first file with the next passed file(s) by their identifiers.')

    args = parser.parse_args()

    try:
        # -i, --inject
        if args.inject:
            if not args.output:
                parser.error("Named argument -o (--output) required.")
                sys.exit(1)

            print("Processing...")
            for path in args.inject:
                if not os.path.exists(path):
                    print(f"Path {path} does not exist")
                    continue

                if not os.path.isdir(path):
                    injection(path, *args.output)
                    continue

                # -r, --recursive
                if args.recursive:
                    for dirpath, dirs, files in os.walk(path):
                        for file in files:
                            path_to_file = os.path.join(path, dirpath, file)
                            extension = os.path.splitext(path_to_file)[1]
                            if extension in VALID_EXTENSIONS:
                                injection(path_to_file, *args.output)

                    continue

                for file in os.listdir(path):
                    path_to_file = os.path.join(path, file)
                    extension = os.path.splitext(path_to_file)[1]
                    if not os.path.isdir(path_to_file) and extension in VALID_EXTENSIONS:
                        injection(path_to_file, *args.output)

            print("Injection completed")

        # -c, --compare
        elif args.compare is not None:
            lhs = args.compare[0]
            if not os.path.exists(lhs):
                print(f"Path {lhs} does not exist")
                exit(1)

            for rhs in args.compare[1:]:
                if not os.path.exists(rhs):
                    print(f"Path {rhs} does not exist")
                    continue

                print(checker.identity_check(lhs, rhs))
        else:
            parser.print_help()

    except Exception as err:
        print(err)
