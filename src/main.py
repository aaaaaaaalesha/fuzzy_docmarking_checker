# Copyright 2022 aaaaaaaalesha
import sys

from src.identifier import injector, checker

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inject', type=str, nargs='+',
                        help='Inject identifier in document(s).')
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
            id_ = injector.IdentifierInjector(path)
            id_.inject_identifier(*args.output)
            print(f"Identifier was injected successfully in document {path}")
        print("Completed")
    elif args.compare:
        print(checker.identity_check(*args.compare))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
