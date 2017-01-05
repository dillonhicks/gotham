GODIR=.go
GOPATH=$(PWD)/$(GODIR)

export PATH:=$(PATH):$(GOPATH)/bin


all:
	exit 1


$(GODIR):
	GOPATH=$(GOPATH) ./install-grpcgateway.sh



grpc-gateway: $(GODIR)



compile-%: grpc-gateway
	GOPATH=$(GOPATH) \
	TARGET_LANGUAGE=$* \
	OUTPUT=build \
	PACKAGE_DIR=tiger \
		$(MAKE) -f grpc.mk


clean:
	find . -type d -name "__pycache__" | xargs rm -rfv
	find . -type d -name '*.egg-info' | xargs rm -rfv
	find . -type f -name "*~" | xargs rm -fv
	$(MAKE) -f grpc.mk clean


really-clean: clean
	rm -rfv $(GODIR)
	$(MAKE) -f grpc.mk really-clean
