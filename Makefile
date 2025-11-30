.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make sync           - Sync dependencies"
	@echo "  make run            - Run the REPL"
	@echo "  make build          - Build the package"
	@echo "  make check          - Run linter"
	@echo "  make release-patch  - Release patch version (0.0.1 -> 0.0.2)"
	@echo "  make release-minor  - Release minor version (0.0.1 -> 0.1.0)"
	@echo "  make release-major  - Release major version (0.0.1 -> 1.0.0)"

.PHONY: sync
sync:
	uv sync

.PHONY: run
run:
	uv run gdrepl

.PHONY: build
build:
	uv build

.PHONY: check
check:
	uv run ruff check gdrepl/

.PHONY: clean
clean:
	rm -rf dist/ build/ *.egg-info/ gdrepl/_version.py .venv/

# Get current version from git tags (supports 3 or 4 part versions)
current_version = $(shell git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' || echo "0.0.0")

# Version bump helper - bumps the last component
define bump_version
	@current=$(current_version); \
	echo "Current version: $$current"; \
	git diff --cached --quiet || (echo "Error: Dirty index. Commit changes first." && exit 1); \
	parts=$$(echo $$current | tr '.' '\n' | wc -l | tr -d ' '); \
	if [ "$$parts" = "4" ]; then \
		p1=$$(echo $$current | cut -d. -f1); \
		p2=$$(echo $$current | cut -d. -f2); \
		p3=$$(echo $$current | cut -d. -f3); \
		p4=$$(echo $$current | cut -d. -f4); \
		case "$(1)" in \
			major) p1=$$((p1 + 1)); p2=0; p3=0; p4=0 ;; \
			minor) p2=$$((p2 + 1)); p3=0; p4=0 ;; \
			patch) p4=$$((p4 + 1)) ;; \
		esac; \
		new_version="$$p1.$$p2.$$p3.$$p4"; \
	else \
		major=$$(echo $$current | cut -d. -f1); \
		minor=$$(echo $$current | cut -d. -f2); \
		patch=$$(echo $$current | cut -d. -f3); \
		case "$(1)" in \
			major) major=$$((major + 1)); minor=0; patch=0 ;; \
			minor) minor=$$((minor + 1)); patch=0 ;; \
			patch) patch=$$((patch + 1)) ;; \
		esac; \
		new_version="$$major.$$minor.$$patch"; \
	fi; \
	echo "New version: $$new_version"; \
	git tag -a "v$$new_version" -m "v$$new_version"; \
	echo "Created tag v$$new_version"; \
	echo "Run 'git push origin v$$new_version' to trigger release"
endef

.PHONY: release-patch
release-patch:
	$(call bump_version,patch)

.PHONY: release-minor
release-minor:
	$(call bump_version,minor)

.PHONY: release-major
release-major:
	$(call bump_version,major)

.PHONY: release-push
release-push:
	@tag=$$(git describe --tags --abbrev=0); \
	echo "Pushing $$tag to origin..."; \
	git push origin $$tag
