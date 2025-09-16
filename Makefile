# Docker image
IMAGE_NAME ?= ghcr.io/mdw-nl/v6-average-py
TAG ?= latest
DOCKERFILE ?= ./Dockerfile

# Debugging
DEBUGPY_DIR ?= tests/v6-dev-profile/debugger/debugpy
LAUNCH_JSON_SRC ?= tests/v6-dev-profile/vscode/launch.json
LAUNCH_JSON_DEST ?= .vscode/launch.json

# Default target
.PHONY: all
all: build

# Build the Docker image
.PHONY: build
build:
	docker build -t $(IMAGE_NAME):$(TAG) -f $(DOCKERFILE) .

# Push the Docker image to registry
.PHONY: push
push:
	docker push $(IMAGE_NAME):$(TAG)

# Download debugpy and install launch.json
install-debug-env:
	@echo "Installing debugpy for later use within containers via volume mount"
	@mkdir -p $(DEBUGPY_DIR)
	@pip install debugpy --target "$(DEBUGPY_DIR)"
	@echo "debugpy installed in $(DEBUGPY_DIR)"
	@echo "Copying launch.json to .vscode directory"
	@mkdir -p .vscode
	@if [ -f "$(LAUNCH_JSON_DEST)" ]; then \
		echo "Error: $(LAUNCH_JSON_DEST) already exists. Refusing to overwrite."; \
		exit 1; \
	fi
	@cp "$(LAUNCH_JSON_SRC)" "$(LAUNCH_JSON_DEST)"
	@echo "launch.json copied to $(LAUNCH_JSON_DEST)"

