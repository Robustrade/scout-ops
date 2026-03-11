import os
import requests
import yaml
import pathlib

kong_admin = os.environ.get("KONG_ADMIN_URL")

def fetch_routes(kong_admin):
    routes = []
    url = f"{kong_admin}/routes"

    while True:
        resp = requests.get(url)
        if resp.status_code != 200:
            raise Exception("Failed to fetch routes")

        body = resp.json()
        routes.extend(body.get("data", []))

        next_page = body.get("next")
        if not next_page:
            break

        url = f"{kong_admin}{next_page}"

    return routes


routes = fetch_routes(kong_admin)

services = {}

for route in routes:
    tags = route.get("tags", [])

    team = None
    service_name = None

    for tag in tags:
        if tag.startswith("team="):
            team = tag.split("=")[1]

        elif tag.endswith("-gateway-backoffice-route"):
            service_name = tag.replace("-gateway-backoffice-route", "")

        elif tag.endswith("-gateway-route"):
            service_name = tag.replace("-gateway-route", "")

        elif tag.endswith("-public-route"):
            service_name = tag.replace("-public-route", "")

        elif tag.endswith("-route"):
            service_name = tag.replace("-route", "")

    if not team or not service_name:
        print(f"Missing team:{team} or service_name:{service_name} or tags:{tags}")
        continue

    service_name = service_name.replace("-", "_")

    api = {
        "name": route.get("name"),
        "methods": route.get("methods", []),
        "paths": route.get("paths", []),
        "service": {"name": service_name},
        "tags": {"team": team},
    }

    key = f"{team}/{service_name}"
    services.setdefault(key, []).append(api)


for key, new_apis in services.items():
    team, service_name = key.split("/")

    dir_path = pathlib.Path(f"teams/{team}/services/{service_name}")
    dir_path.mkdir(parents=True, exist_ok=True)

    file_path = dir_path / "api.yaml"

    existing_apis = []

    if file_path.exists():
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
            if data and "apis" in data:
                existing_apis = data["apis"]

    existing_names = {api["name"] for api in existing_apis}

    for api in new_apis:
        if api["name"] not in existing_names:
            existing_apis.append(api)
            existing_names.add(api["name"])

    existing_apis.sort(key=lambda x: x["name"])

    with open(file_path, "w") as f:
        yaml.dump({"apis": existing_apis}, f, sort_keys=False)

print("Kong routes synced successfully without duplicates.")