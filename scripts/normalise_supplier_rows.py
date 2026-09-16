#!/usr/bin/env python3
import argparse
from aromatwin.services.normalisation import split_variant

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("names", nargs="+")
    args = parser.parse_args()
    for value in args.names:
        print(*split_variant(value), sep="\t")
