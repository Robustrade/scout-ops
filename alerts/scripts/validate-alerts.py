#!/usr/bin/env python3
"""Validate team-based API and SLA spec files."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_yaml(path: Path):
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


def validate_duration(value, field_name, file_path):
    if not isinstance(value, str):
        print(f"ERROR: {file_path}: {field_name} must be a string, got {type(value).__name__}")
        return 1
    if not value:
        print(f"ERROR: {file_path}: {field_name} must not be empty")
        return 1
    if not value[:-1].isdigit() or value[-1] not in ("s", "m", "h"):
        print(f"ERROR: {file_path}: {field_name} must be '<int><s|m|h>', got '{value}'")
        return 1
    return 0


def validate_slo_entry(slo, api_name, file_path):
    failures = 0
    for slo_type in ("error_rate", "latency"):
        if slo_type not in slo:
            continue
        entry = slo[slo_type]
        prefix = f"{file_path}: {api_name}.slo.{slo_type}"
        if not isinstance(entry, dict):
            print(f"ERROR: {prefix} must be an object")
            failures += 1
            continue
        threshold = entry.get("threshold")
        if not isinstance(threshold, (int, float)) or threshold <= 0:
            print(f"ERROR: {prefix}.threshold must be a positive number")
            failures += 1
        if "operator" not in entry or not isinstance(entry["operator"], str):
            print(f"ERROR: {prefix}.operator must be a string")
            failures += 1
        if "unit" not in entry or not isinstance(entry["unit"], str):
            print(f"ERROR: {prefix}.unit must be a string")
            failures += 1
        if "window" in entry:
            failures += validate_duration(entry["window"], f"{api_name}.slo.{slo_type}.window", file_path)
        if "alert" in entry and not isinstance(entry["alert"], bool):
            print(f"ERROR: {prefix}.alert must be a boolean")
            failures += 1
    return failures


def validate_global_sla(spec_dir: Path):
    sla_path = spec_dir / "sla.yaml"
    if not sla_path.exists():
        print(f"ERROR: global SLA file not found: {sla_path}")
        return 1
    failures = 0
    try:
        data = load_yaml(sla_path)
    except Exception as err:
        print(f"ERROR: {sla_path}: {err}")
        return 1
    apis = data.get("apis")
    if not isinstance(apis, list) or not apis:
        print(f"ERROR: {sla_path}: 'apis' must be a non-empty list")
        return 1
    wildcard_found = False
    for api in apis:
        name = api.get("name")
        if name == "*":
            wildcard_found = True
        slo = api.get("slo")
        if not isinstance(slo, dict):
            print(f"ERROR: {sla_path}: api '{name}' must have 'slo' object")
            failures += 1
            continue
        failures += validate_slo_entry(slo, name, sla_path)
    if not wildcard_found:
        print(f"ERROR: {sla_path}: must have a wildcard ('*') entry for defaults")
        failures += 1
    return failures


def validate_team_api(api_path: Path):
    failures = 0
    api_names = []
    try:
        data = load_yaml(api_path)
    except Exception as err:
        print(f"ERROR: {api_path}: {err}")
        return 1, []
    apis = data.get("apis")
    if not isinstance(apis, list) or not apis:
        print(f"ERROR: {api_path}: 'apis' must be a non-empty list")
        return 1, []
    for api in apis:
        name = api.get("name")
        if not isinstance(name, str) or not name:
            print(f"ERROR: {api_path}: each api must have a 'name' string")
            failures += 1
            continue
        api_names.append(name)
        paths = api.get("paths")
        if not isinstance(paths, list) or not paths:
            print(f"ERROR: {api_path}: api '{name}' must have 'paths' list")
            failures += 1
        methods = api.get("methods")
        if not isinstance(methods, list) or not methods:
            print(f"ERROR: {api_path}: api '{name}' must have 'methods' list")
            failures += 1
        service = api.get("service")
        if not isinstance(service, dict) or not service.get("name"):
            print(f"ERROR: {api_path}: api '{name}' must have 'service.name'")
            failures += 1
        tags = api.get("tags")
        if not isinstance(tags, dict) or not tags.get("team"):
            print(f"ERROR: {api_path}: api '{name}' must have 'tags.team'")
            failures += 1
    return failures, api_names


def validate_team_sla(sla_path: Path, valid_api_names: list):
    if not sla_path.exists():
        return 0
    failures = 0
    try:
        data = load_yaml(sla_path)
    except Exception as err:
        print(f"ERROR: {sla_path}: {err}")
        return 1
    apis = data.get("apis")
    if not isinstance(apis, list):
        print(f"ERROR: {sla_path}: 'apis' must be a list")
        return 1
    for api in apis:
        name = api.get("name")
        if not isinstance(name, str) or not name:
            print(f"ERROR: {sla_path}: each api must have a 'name' string")
            failures += 1
            continue
        if name not in valid_api_names:
            print(f"ERROR: {sla_path}: api '{name}' not found in team's api.yaml")
            failures += 1
        slo = api.get("slo")
        if not isinstance(slo, dict):
            print(f"ERROR: {sla_path}: api '{name}' must have 'slo' object")
            failures += 1
            continue
        failures += validate_slo_entry(slo, name, sla_path)
    return failures


def validate_all(spec_dir: Path) -> int:
    failures = 0
    teams_dir = spec_dir / "teams"

    # Validate global SLA
    failures += validate_global_sla(spec_dir)

    # Find teams
    if not teams_dir.is_dir():
        print(f"ERROR: teams directory not found: {teams_dir}")
        return failures + 1

    team_dirs = sorted([d for d in teams_dir.iterdir() if d.is_dir()])
    if not team_dirs:
        print(f"ERROR: no team directories found in {teams_dir}")
        return failures + 1

    all_api_names = {}
    total_apis = 0

    for team_dir in team_dirs:
        team_name = team_dir.name
        api_path = team_dir / "api.yaml"
        sla_path = team_dir / "sla.yaml"

        if not api_path.exists():
            print(f"ERROR: {team_name}: api.yaml not found in {team_dir}")
            failures += 1
            continue

        errs, api_names = validate_team_api(api_path)
        failures += errs
        total_apis += len(api_names)

        # Check for duplicate API names across teams
        for name in api_names:
            if name in all_api_names:
                print(f"ERROR: duplicate API name '{name}' in {team_name} and {all_api_names[name]}")
                failures += 1
            else:
                all_api_names[name] = team_name

        # Validate team SLA (optional file)
        failures += validate_team_sla(sla_path, api_names)

    if failures:
        print(f"Validation failed with {failures} error(s)")
        return 1

    print(f"Validation passed: {len(team_dirs)} team(s), {total_apis} API(s)")
    return 0


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return validate_all(Path(args.spec_dir))


if __name__ == "__main__":
    raise SystemExit(main())
