#!/usr/bin/env python3
"""Validate endpoint alert specs and repository rules."""

import argparse
import subprocess
from pathlib import Path

import json


def load_yaml(path: Path):
    # Use system Ruby (Psych) to avoid external Python YAML dependency.
    cmd = [
        "/usr/bin/ruby",
        "-ryaml",
        "-rjson",
        "-e",
        "puts JSON.generate(YAML.load_file(ARGV[0]))",
        str(path),
    ]
    raw = subprocess.check_output(cmd, text=True)
    data = json.loads(raw)
    if data is None:
        raise ValueError("file is empty")
    if not isinstance(data, dict):
        raise ValueError("top-level YAML must be an object")
    return data


def validate_alert(alert, file_path: Path):
    failures = 0
    if not isinstance(alert, dict):
        print(f"ERROR: {file_path}: each alert must be an object")
        return 1
    if alert.get("type") != "latency":
        print(f"ERROR: {file_path}: alert.type must be 'latency'")
        failures += 1
    threshold = alert.get("threshold_ms")
    if not isinstance(threshold, (int, float)) or threshold <= 0:
        print(f"ERROR: {file_path}: alert.threshold_ms must be a positive number")
        failures += 1
    for key in ("eval_interval", "lookback", "pendingPeriod", "keepFiringFor"):
        if key in alert:
            value = alert.get(key)
            if not isinstance(value, str):
                print(f"ERROR: {file_path}: {key} must be a string")
                failures += 1
            elif key != "keepFiringFor" and not value[:-1].isdigit():
                print(f"ERROR: {file_path}: {key} must look like '<int><s|m|h>'")
                failures += 1
            elif key != "keepFiringFor" and value[-1] not in ("s", "m", "h"):
                print(f"ERROR: {file_path}: {key} must end with s, m, or h")
                failures += 1
            elif key == "keepFiringFor" and value != "":
                if not value[:-1].isdigit() or value[-1] not in ("s", "m", "h"):
                    print(f"ERROR: {file_path}: keepFiringFor must be '' or '<int><s|m|h>'")
                    failures += 1
    return failures


def validate_files(spec_dir: Path, _schema_path: Path) -> int:
    endpoint_to_file = {}
    failures = 0

    files = sorted(spec_dir.glob("*.yml")) + sorted(spec_dir.glob("*.yaml"))
    if not files:
        print(f"ERROR: no spec files found in {spec_dir}")
        return 1

    for file_path in files:
        try:
            data = load_yaml(file_path)
        except Exception as err:
            print(f"ERROR: {file_path}: {err}")
            failures += 1
            continue

        endpoint = data.get("endpoint")
        alerts = data.get("alerts")
        if not isinstance(endpoint, str) or not endpoint:
            print(f"ERROR: {file_path}: endpoint is required and must be a string")
            failures += 1
        if not isinstance(alerts, list) or not alerts:
            print(f"ERROR: {file_path}: alerts is required and must be a non-empty list")
            failures += 1
        elif isinstance(alerts, list):
            for alert in alerts:
                failures += validate_alert(alert, file_path)

        if isinstance(endpoint, str):
            if not endpoint.startswith("/"):
                print(f"ERROR: {file_path}: endpoint must start with '/': {endpoint}")
                failures += 1
            if endpoint in endpoint_to_file:
                print(
                    "ERROR: duplicate endpoint "
                    f"{endpoint} in {file_path} and {endpoint_to_file[endpoint]}"
                )
                failures += 1
            else:
                endpoint_to_file[endpoint] = file_path

    if failures:
        print(f"Validation failed with {failures} error(s)")
        return 1

    print(f"Validation passed for {len(files)} file(s)")
    return 0


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-dir", required=True)
    parser.add_argument("--schema", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return validate_files(Path(args.spec_dir), Path(args.schema))


if __name__ == "__main__":
    raise SystemExit(main())
