#!/usr/bin/env python3
"""Future entry point for licensed catalogue exports."""

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.parse_args()
    print("Catalogue export is not implemented in the foundation release.")
