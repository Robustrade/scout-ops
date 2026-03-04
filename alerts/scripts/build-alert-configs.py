#!/usr/bin/env python3
"""Build Jsonnet inputs from endpoint alert spec files."""

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


def render_query(template: str, endpoint: str, env: str, table: str) -> str:
    return template.format(endpoint=endpoint, env=env, table=table)


def build_outputs(spec_dir: Path, global_config_path: Path):
    global_config = load_yaml(global_config_path)

    envs = global_config["envArray"]
    platform_cfg = global_config["alertPlatform"]
    defaults = global_config["defaults"]
    ds_cfg = global_config["datasource"]

    default_eval_interval = defaults["latency"]["eval_interval"]
    default_lookback = defaults["latency"]["lookback"]
    default_severity = defaults["latency"]["severity"]
    default_pending_period = defaults["alerting"]["pendingPeriod"]
    default_keep_firing_for = defaults["alerting"]["keepFiringFor"]
    default_no_data_state = defaults["alerting"]["noDataState"]
    default_exec_err_state = defaults["alerting"]["execErrState"]

    files = sorted(spec_dir.glob("*.yml")) + sorted(spec_dir.glob("*.yaml"))

    grouped_rules = defaultdict(list)

    for file_path in files:
        spec = load_yaml(file_path)
        endpoint = spec["endpoint"]

        for alert in spec["alerts"]:
            if alert["type"] != "latency":
                continue

            for env in envs:
                eval_interval = alert.get("eval_interval", default_eval_interval)
                interval_seconds = parse_duration_seconds(eval_interval)
                lookback = alert.get("lookback", default_lookback)
                lookback_seconds = parse_duration_seconds(lookback)
                severity = alert.get("severity", default_severity)
                threshold = alert["threshold_ms"]
                table = alert.get("table", ds_cfg["table"])

                labels = dict(platform_cfg.get("labels", {}))
                labels.update({
                    "env": env,
                    "endpoint": endpoint,
                    "severity": severity,
                    "alert_type": "latency",
                })
                labels.update(alert.get("labels", {}))

                query_template = alert.get("query_template", ds_cfg["queryTemplate"])
                rule = {
                    "title": f"High Latency {endpoint} ({env})",
                    "labels": labels,
                    "evaluator": {"type": "gt", "params": [threshold]},
                    "annotations": {
                        "summary": f"High latency for {endpoint} in {env}",
                        "description": (
                            f"Latency for {endpoint} exceeded {threshold}ms in {env}."
                        ),
                    },
                    "query": render_query(query_template, endpoint, env, table),
                    "relativeTimeRange": {"from": lookback_seconds, "to": 0},
                    "dateTimeColDataType": ds_cfg["dateTimeColDataType"],
                    "dateTimeType": ds_cfg["dateTimeType"],
                    "format": ds_cfg["format"],
                    "table": table,
                    "pendingPeriod": alert.get("pendingPeriod", default_pending_period),
                    "keepFiringFor": alert.get("keepFiringFor", default_keep_firing_for),
                    "noDataState": alert.get("noDataState", default_no_data_state),
                    "execErrState": alert.get("execErrState", default_exec_err_state),
                    "folderUid": alert.get("folderUid", platform_cfg["folderUid"]),
                    "contactPoint": alert.get("contactPoint", platform_cfg["contactPoint"]),
                }

                grouped_rules[(env, interval_seconds)].append(rule)

    alert_groups = []
    for (env, interval_seconds), rules in sorted(grouped_rules.items()):
        alert_groups.append(
            {
                "name": f"endpoint-latency-{env}-{interval_seconds}s",
                "interval": interval_seconds,
                "alertRules": rules,
            }
        )

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
