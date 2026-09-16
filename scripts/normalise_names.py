#!/usr/bin/env python3
import argparse

from scentgraph.services.importer import normalise_name

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("names", nargs="+")
    args = parser.parse_args()
    for name in args.names:
        print(normalise_name(name))
