RUNNER := docker
IMAGE_BUILDER := $(RUNNER) buildx
MACHINE := neuvector
BUILDX_ARGS ?= --sbom=true --attest type=provenance,mode=max --cache-to type=gha --cache-from type=gha
DEFAULT_PLATFORMS := linux/amd64,linux/arm64,linux/x390s,linux/riscv64
TARGET_PLATFORMS ?= linux/amd64,linux/arm64
STAGE_DIR=stage

REPO ?= neuvector

COMMIT = $(shell git rev-parse --short HEAD)
ifeq ($(VERSION),)
	# Define VERSION, which is used for image tags or to bake it into the
	# compiled binary to enable the printing of the application version, 
	# via the --version flag.
	CHANGES = $(shell git status --porcelain --untracked-files=no)
	ifneq ($(CHANGES),)
		DIRTY = -dirty
	endif


	COMMIT = $(shell git rev-parse --short HEAD)
	VERSION = $(COMMIT)$(DIRTY)

	# Override VERSION with the Git tag if the current HEAD has a tag pointing to
	# it AND the worktree isn't dirty.
	GIT_TAG = $(shell git tag -l --contains HEAD | head -n 1)
	ifneq ($(GIT_TAG),)
		ifeq ($(DIRTY),)
			VERSION = $(GIT_TAG)
		endif
	endif
endif

ifeq ($(TAG),)
	TAG = $(VERSION)
	ifneq ($(DIRTY),)
		TAG = dev
	endif
endif

buildx-machine:
	docker buildx ls
	@docker buildx ls | grep $(MACHINE) || \
	docker buildx create --name=$(MACHINE) --platform=$(DEFAULT_PLATFORMS)


push-image: buildx-machine
	$(IMAGE_BUILDER) build -f package/Dockerfile \
		--builder $(MACHINE) $(IMAGE_ARGS) $(IID_FILE_FLAG) $(BUILDX_ARGS) \
		--build-arg VERSION=$(VERSION) --build-arg COMMIT=$(COMMIT) --platform=$(TARGET_PLATFORMS) -t "$(REPO)/prometheus-exporter:$(TAG)" --push .
	@echo "Pushed $(IMAGE)"
