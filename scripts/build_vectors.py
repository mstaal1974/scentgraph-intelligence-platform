#!/usr/bin/env python3
"""Future entry point for versioned vector derivation; intentionally performs no inference yet."""

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.parse_args()
    print("Vector building is not implemented in the foundation release.")
