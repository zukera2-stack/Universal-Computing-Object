import argparse
import json
from . import run

def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result

def load(path):
    with open(path, "rb") as file:
        data = file.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError("JSON size limit")
    return json.loads(data, object_pairs_hook=pairs)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--object", required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--grant", action="append", default=[])
    args = parser.parse_args()
    try:
        print(json.dumps(run(load(args.object), load(args.device), args.grant), sort_keys=True))
    except (ValueError, OSError, RecursionError) as error:
        parser.exit(2, f"error: {error}\n")

if __name__ == "__main__":
    main()
