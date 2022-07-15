# Copyright 2022 aaaaaaaalesha

import sys
import os.path

import argparse
from typing import Callable

from src.identifier import injector, checker
from constants import VALID_EXTENSIONS


def injection(out_dir: str, path_to_file: str, to_file=None) -> None:
    id_ = injector.IdentifierInjector(path_to_file)
    id_.inject_identifier(out_dir)
    print(f"Identifier was injected successfully in file {os.path.basename(path_to_file)} "
          f"and moved in out directory {os.path.abspath(out_dir)}")


def compare(lhs: str, rhs: str, to_file=None) -> None:
    print(checker.identity_check(lhs, rhs, to_file))


def recursive_handler(target_dir: str, func: Callable, first_arg, to_file=None) -> None:
    for dirpath, dirs, files in os.walk(target_dir):
        for file in files:
            path_to_file = os.path.join(target_dir, dirpath, file)
            extension = os.path.splitext(path_to_file)[1]
            if extension in VALID_EXTENSIONS:
                try:
                    func(first_arg, path_to_file, to_file)
                except Exception as err:
                    print(err)


def straight_handler(target_dir: str, func: Callable, first_arg, to_file=None) -> None:
    for file in os.listdir(target_dir):
        path_to_file = os.path.join(target_dir, file)
        extension = os.path.splitext(path_to_file)[1]
        if not os.path.isdir(path_to_file) and extension in VALID_EXTENSIONS:
            try:
                func(first_arg, path_to_file, to_file)
            except Exception as err:
                print(err)


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
    parser.add_argument('-wr', '--write_results', type=str, nargs=1,
                        help='Writing compare results to passed .csv file')

    args = parser.parse_args()

    try:
        # -i, --inject
        if args.inject:
            if not args.output:
                parser.error("Named argument -o (--output) required")
                sys.exit(1)

            print("Processing...")
            for path in args.inject:
                if not os.path.exists(path):
                    print(f"Path {path} does not exist")
                    continue

                if not os.path.isdir(path):
                    injection(*args.output, path)
                    continue

                # -r, --recursive
                if args.recursive:
                    recursive_handler(path, injection, *args.output)
                    continue

                straight_handler(path, injection, *args.output)

            print("Injection completed")

        # -c, --compare
        elif args.compare is not None:
            to_file = None
            if args.write_results:
                to_file = args.write_results[0]
                ext = os.path.splitext(to_file)[1]

                if not ext == '.csv':
                    print(f"File {to_file} should have .csv extension")
                    exit(1)

            # First argument is always target file.
            lhs = args.compare[0]
            if not os.path.exists(lhs):
                print(f"Path {lhs} does not exist")
                exit(1)

            if os.path.isdir(lhs):
                print(f"{lhs} should be a target file, not directory")
                exit(1)

            for rhs in args.compare[1:]:
                if not os.path.exists(rhs):
                    print(f"Path {rhs} does not exist")
                    continue

                if not os.path.isdir(rhs):
                    try:
                        print(checker.identity_check(lhs, rhs, to_file))
                    except Exception as err:
                        print(err)

                # -r, --recursive
                if args.recursive:
                    recursive_handler(rhs, compare, lhs, to_file)
                    continue

                straight_handler(rhs, compare, lhs, to_file)

        else:
            parser.print_help()

    except Exception as err:
        print(err)
