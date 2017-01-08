GODIR=.go
GOPATH=$(PWD)/$(GODIR)

export PATH:=$(PATH):$(GOPATH)/bin
PACKAGE_DIR ?= tiger


all:
	exit 1


$(GODIR):
	GOPATH=$(GOPATH) ./install-grpcgateway.sh



grpc-gateway: $(GODIR)



compile-%: grpc-gateway
	GOPATH=$(GOPATH) \
	TARGET_LANGUAGE=$* \
	OUTPUT=build \
	PACKAGE_DIR=$(PACKAGE_DIR) \
		$(MAKE) -f grpc.mk


clean:
	find . -type d -name "__pycache__" | xargs rm -rfv
	find . -type d -name '*.egg-info' | xargs rm -rfv
	find . -type f -name "*~" | xargs rm -fv
	$(MAKE) -f grpc.mk clean


really-clean: clean
	rm -rfv $(GODIR)
	$(MAKE) -f grpc.mk really-clean


docker-test:
	docker run \
		-v $(PWD)/config:/app/config \
		-v $(PWD)/protos:/app/protos \
		-v $(PWD)/dockerbuild:/app/build \
		-e USERID=1000g \
		-e USER=$(USER) \
		--rm \
		-t dillonhicks/gotham:latest
