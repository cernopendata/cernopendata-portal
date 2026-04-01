#!/usr/bin/env python3

import json
import sys

from jsonschema import Draft7Validator


def load_schema(schema_path):
    with open(schema_path) as f:
        return json.load(f)


def validate_files(schema, file_paths):
    validator = Draft7Validator(schema)
    total_processed = 0

    for file_path in file_paths:
        #        print(f"Processing file: {file_path}", file=sys.stderr)

        with open(file_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse file {file_path}: {e}")
                continue

        if not isinstance(data, list):
            print(f"❌ File {file_path} does not contain a JSON list")
            continue

        for idx, item in enumerate(data):
            total_processed += 1

            errors = list(validator.iter_errors(item))
            if errors:
                print(f"❌ File: {file_path}, item #{idx}")
                for e in errors:
                    path = ".".join(str(p) for p in e.path)
                    print(f"   - {path or '<root>'}: {e.message}")

            # Heartbeat every 1000 records
            if total_processed % 1000 == 0:
                print(
                    f"[heartbeat] Processed {total_processed} records", file=sys.stderr
                )

    print(f"Done. Total records processed: {total_processed}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: validate.py schema.json file1.json file2.json ...")
        sys.exit(1)

    schema_path = sys.argv[1]
    file_paths = sys.argv[2:]

    schema = load_schema(schema_path)
    validate_files(schema, file_paths)
