#!/usr/bin/env python3
"""Build Jsonnet inputs from team-based API and SLA spec files."""

import argparse
import json
import subprocess
from collections import defaultdict
from pathlib import Path


def parse_duration_seconds(value: str) -> int:
    if value == "":
        return 0
    unit = value[-1]
    amount = int(value[:-1])
    if unit == "s":
        return amount
    if unit == "m":
        return amount * 60
    if unit == "h":
        return amount * 3600
    raise ValueError(f"unsupported duration '{value}', expected suffix s/m/h")


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
    return json.loads(raw)


def render_query(template: str, endpoint: str, env: str, table: str, team: str = "") -> str:
    return template.format(endpoint=endpoint, env=env, table=table, team=team)


def load_global_sla(spec_dir: Path) -> dict:
    """Load global SLA and return dict of {api_name: {slo_type: slo_config}}."""
    data = load_yaml(spec_dir / "sla.yaml")
    result = {}
    for api in data["apis"]:
        result[api["name"]] = api["slo"]
    return result


def load_team_sla(team_dir: Path) -> dict:
    """Load team SLA if exists. Returns dict of {api_name: {slo_type: slo_config}}."""
    sla_path = team_dir / "sla.yaml"
    if not sla_path.exists():
        return {}
    data = load_yaml(sla_path)
    result = {}
    for api in data.get("apis", []):
        result[api["name"]] = api["slo"]
    return result


def resolve_slo(api_name: str, team_sla: dict, global_sla: dict) -> dict:
    """Resolve SLO for an API. Team SLA overrides global per slo_type."""
    global_defaults = global_sla.get("*", {})
    team_api_slo = team_sla.get(api_name, {})

    resolved = {}
    for slo_type in ("error_rate", "latency"):
        if slo_type in team_api_slo:
            resolved[slo_type] = team_api_slo[slo_type]
        elif slo_type in global_defaults:
            resolved[slo_type] = global_defaults[slo_type]
    return resolved


def format_threshold_display(threshold, unit: str) -> str:
    if unit == "percent":
        return f"{threshold}%"
    if unit == "ms":
        return f"{threshold}ms"
    if unit == "s":
        return f"{threshold}s"
    return f"{threshold} {unit}"


SLO_TYPE_LABELS = {
    "error_rate": "error rate",
    "latency": "latency",
}


def build_outputs(spec_dir: Path, global_config_path: Path):
    global_config = load_yaml(global_config_path)

    envs = global_config["envArray"]
    platform_cfg = global_config["alertPlatform"]
    alerting_defaults = global_config["defaults"]["alerting"]
    ds_cfg = global_config["datasource"]

    global_sla = load_global_sla(spec_dir)
    teams_dir = spec_dir / "teams"
    team_dirs = sorted([d for d in teams_dir.iterdir() if d.is_dir()])

    grouped_rules = defaultdict(list)

    for team_dir in team_dirs:
        api_data = load_yaml(team_dir / "api.yaml")
        team_sla = load_team_sla(team_dir)

        for api in api_data["apis"]:
            api_name = api["name"]
            api_paths = api["paths"]
            api_tags = api.get("tags", {})
            service_name = api.get("service", {}).get("name", "")
            endpoint = api_paths[0]

            resolved = resolve_slo(api_name, team_sla, global_sla)

            for slo_type, slo_cfg in resolved.items():
                if not slo_cfg.get("alert", False):
                    continue

                for env in envs:
                    threshold = slo_cfg["threshold"]
                    unit = slo_cfg["unit"]
                    window = slo_cfg.get("window", "5m")
                    window_seconds = parse_duration_seconds(window)
                    display = format_threshold_display(threshold, unit)
                    human_type = SLO_TYPE_LABELS.get(slo_type, slo_type)

                    eval_interval = window
                    interval_seconds = parse_duration_seconds(eval_interval)
                    lookback_seconds = window_seconds
                    table = ds_cfg["tables"][slo_type]

                    labels = dict(platform_cfg.get("labels", {}))
                    labels.update({
                        "env": env,
                        "api_name": api_name,
                        "endpoint": endpoint,
                        "alert_type": slo_type,
                        "service": service_name,
                    })
                    labels.update(api_tags)

                    query_template = ds_cfg["queryTemplates"][slo_type]
                    evaluator_type = "gt" if slo_cfg.get("operator", ">") == ">" else "lt"
                    team = api_tags.get("team", "")

                    rule = {
                        "title": f"{api_name} {human_type} above {display}",
                        "labels": labels,
                        "evaluator": {"type": evaluator_type, "params": [threshold]},
                        "annotations": {
                            "summary": f"{api_name} {human_type} above {display} in {env}",
                            "description": (
                                f"{human_type.capitalize()} for {api_name} "
                                f"({endpoint}) exceeded {display} in {env}."
                            ),
                        },
                        "query": render_query(query_template, endpoint, env, table, team=team),
                        "relativeTimeRange": {"from": lookback_seconds, "to": 0},
                        "dateTimeColDataType": ds_cfg["dateTimeColDataType"],
                        "dateTimeType": ds_cfg["dateTimeType"],
                        "format": ds_cfg["format"],
                        "table": table,
                        "pendingPeriod": alerting_defaults["pendingPeriod"],
                        "keepFiringFor": alerting_defaults["keepFiringFor"],
                        "noDataState": alerting_defaults["noDataState"],
                        "execErrState": alerting_defaults["execErrState"],
                        "folderUid": platform_cfg["folderUid"],
                        "contactPoint": platform_cfg["contactPoint"],
                    }

                    grouped_rules[(env, interval_seconds)].append(rule)

    alert_groups = []
    for (env, interval_seconds), rules in sorted(grouped_rules.items()):
        alert_groups.append({
            "name": f"api-alerts-{env}-{interval_seconds}s",
            "interval": interval_seconds,
            "alertRules": rules,
        })

    alert_configs = {"alertGroups": alert_groups}
    team_config = {
        "folderUid": platform_cfg["folderUid"],
        "labels": {},
        "contactPoint": platform_cfg["contactPoint"],
    }

    return alert_configs, team_config


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-dir", required=True)
    parser.add_argument("--global-config", required=True)
    parser.add_argument("--alert-configs-out", required=True)
    parser.add_argument("--team-config-out", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    alert_configs, team_config = build_outputs(
        spec_dir=Path(args.spec_dir),
        global_config_path=Path(args.global_config),
    )
    with Path(args.alert_configs_out).open("w", encoding="utf-8") as f:
        json.dump(alert_configs, f, indent=2)
    with Path(args.team_config_out).open("w", encoding="utf-8") as f:
        json.dump(team_config, f, indent=2)
    print(f"Wrote {args.alert_configs_out} and {args.team_config_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
