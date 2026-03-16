SPEC_DIR ?= ../specs
GLOBAL_CONFIG ?= configs/global.yaml
GENERATED_DIR ?= generated
TEAM ?=
API ?=
LIMIT ?=
_TEAM_SUFFIX := $(if $(TEAM),-$(TEAM),)
ALERT_CONFIGS_JSON ?= $(GENERATED_DIR)/alert-configs$(_TEAM_SUFFIX).json
TEAM_CONFIG_JSON ?= $(GENERATED_DIR)/team-config.json
RESOURCES_JSON ?= $(GENERATED_DIR)/resources$(_TEAM_SUFFIX).json

validate:
	@echo "=== Validating specs ==="
	python3 scripts/validate-alerts.py \
		--spec-dir "$(SPEC_DIR)"

build-inputs: validate
	@echo "=== Building alert inputs$(if $(TEAM), for team: $(TEAM),) ==="
	@mkdir -p "$(GENERATED_DIR)"
	python3 scripts/build-alert-configs.py \
		--spec-dir "$(SPEC_DIR)" \
		--global-config "$(GLOBAL_CONFIG)" \
		--alert-configs-out "$(ALERT_CONFIGS_JSON)" \
		--team-config-out "$(TEAM_CONFIG_JSON)" \
		$(if $(TEAM),--team "$(TEAM)",) \
		$(if $(API),--api "$(API)",) \
		$(if $(LIMIT),--limit "$(LIMIT)",)

generate: build-inputs
	@echo "=== Rendering resources ==="
	jsonnet \
		--ext-str-file ALERT_CONFIGS="$(ALERT_CONFIGS_JSON)" \
		--ext-str-file TEAM_CONFIGS="$(TEAM_CONFIG_JSON)" \
		main.jsonnet > "$(RESOURCES_JSON)"
	@echo "$(RESOURCES_JSON) ready for diff/apply"

diff: generate
	grr diff "$(RESOURCES_JSON)"

apply: generate
	grr apply "$(RESOURCES_JSON)"

config:
	grr config create-context scout
	grr config set grafana.url "$${ALERT_PLATFORM_URL}"
	grr config set grafana.token "$${ALERT_PLATFORM_TOKEN}"
	grr config set targets AlertRuleGroup

clean:
	rm -rf "$(GENERATED_DIR)"
