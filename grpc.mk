SHELL := /usr/bin/env bash

PROTOBUF_COMMON_LIB_REPO=https://github.com/googleapis/googleapis.git
GOOGLEAPIS=googleapis
# PROTOC ?=./.local/protoc/bin/protoc
PROTOC=python -m grpc.tools.protoc

# Source Directories
PROTOS_DIR ?= protos
PACKAGE_DIR ?= tiger
SWAGGER_DIR ?= swagger
GRPC_DIR ?= grpc
TEMPLATES_DIR ?= $(PWD)/templates

# Choose the target language.
TARGET_LANGUAGE ?= python

# Choose the output directory
OUTPUT ?= gens
OUTPUT := $(OUTPUT)/$(TARGET_LANGUAGE)
_:= $(shell mkdir -p $(OUTPUT)/../grpc)
OUTPUT_GRPC_GATEWAY = $(shell readlink -f $(OUTPUT)/../$(GRPC_DIR))
OUTPUT_SWAGGER = $(shell readlink -f $(OUTPUT)/../$(SWAGGER_DIR))
GOPATH=$(OUTPUT_GRPC_GATEWAY)
GOBIN=$(OUTPUT_GRPC_GATEWAY)/bin


ifeq ($(TARGET_LANGUAGE), python)

SUFFIX := pb2.py

else ifeq ($(TARGET_LANGUAGE), go)

SUFFIX := pb.go

else
	$(error 'Unable to determine suffix')
endif


FLAGS+= --$(TARGET_LANGUAGE)_out=$(OUTPUT) \
	--proto_path=$(PROTOS_DIR) \
	--proto_path=$(GOOGLEAPIS)


DEPS:= $(shell find $(PROTOS_DIR) -type f -name '*.proto')


compile: $(PROTOC) $(GOOGLEAPIS) sources packaging-$(TARGET_LANGUAGE)


REST_PROXY_NAME=rest-proxy-server.bin
export GOPATH
export GOBIN
packaging-python:
	cd $(OUTPUT) && \
		mkdir -p $(PACKAGE_DIR) && \
		mv $(PACKAGE_DIR) $(PACKAGE_DIR).bak && \
		mkdir $(PACKAGE_DIR) && \
		mv $(PACKAGE_DIR).bak $(PACKAGE_DIR)/$(PACKAGE_DIR) && \
		mv setup.py $(PACKAGE_DIR) && \
		mv bin $(PACKAGE_DIR)
	cd $(OUTPUT_GRPC_GATEWAY) && \
		mkdir -p src && \
		mv $(PACKAGE_DIR) src && \
		 go get . && \
		go build -o $(REST_PROXY_NAME) -buildmode pie main.go
	mkdir -p $(OUTPUT)/$(PACKAGE_DIR)/$(PACKAGE_DIR)/bin
	cp -R $(OUTPUT_SWAGGER)/$(PACKAGE_DIR)/* $(OUTPUT)/$(PACKAGE_DIR)/$(PACKAGE_DIR)/
	cp $(OUTPUT_GRPC_GATEWAY)/$(REST_PROXY_NAME) $(OUTPUT)/$(PACKAGE_DIR)/$(PACKAGE_DIR)/bin
	cd $(OUTPUT)/$(PACKAGE_DIR) && \
		python setup.py bdist_wheel && \
		mv dist/*.whl ../../


packaging-go:
	echo 'GO!'


$(GOOGLEAPIS):
	git clone $(PROTOBUF_COMMON_LIB_REPO) $(GOOGLEAPIS)


$(PROTOC):
	./install-protoc.sh


$(OUTPUT):
	mkdir -p $(OUTPUT)


$(OUTPUT_GRPC_GATEWAY):
	mkdir -p $(OUTPUT_GRPC_GATEWAY)

sources:
	mkdir -p $(OUTPUT)/bin
	mkdir -p $(OUTPUT_GRPC_GATEWAY)
	mkdir -p $(OUTPUT_SWAGGER)
	$(PROTOC) \
		$(FLAGS) \
		--proto_path=$(GOPATH)/src \
		--proto_path=$(GOPATH)/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
		--go_out=Mgoogle/api/annotations.proto=github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis/google/api,plugins=grpc:$(OUTPUT_GRPC_GATEWAY) \
		--grpc-gateway_out=logtostderr=true:$(OUTPUT_GRPC_GATEWAY) \
		--grpc_$(TARGET_LANGUAGE)_out=$(OUTPUT) \
		 --swagger_out=logtostderr=true:$(OUTPUT_SWAGGER) \
		$(DEPS)
	find $(OUTPUT) -type d | grep -v '$(OUTPUT)$$' | xargs -I{} touch {}/__init__.py
	python render.py --file $(TEMPLATES_DIR)/{{grpc_json_proxy_name}}.go --out $(OUTPUT_GRPC_GATEWAY)
	python render.py --file $(TEMPLATES_DIR)/{{server.rest_proxy_script}} --out $(OUTPUT)/bin
	python render.py --file $(TEMPLATES_DIR)/setup.py --out $(OUTPUT)
	python render.py --file $(TEMPLATES_DIR)/client.py --out $(OUTPUT)/$(PACKAGE_DIR)
	python render.py --file $(TEMPLATES_DIR)/server-stubs.py --out $(OUTPUT)


clean:
	-rm -rvf gens
	-rm -rvf gen-*
	-rm -rfv build

really-clean: clean
	-rm -rfv $(GOOGLEAPIS)
	-rm -rfv ./.local
