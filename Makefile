proto: obs/proto/openbikesensor.py

obs/proto/openbikesensor.py:
	protoc openbikesensor.proto --python_out=./obs/proto/

install-dev: proto
	pip install -e .

install: proto
	pip install .


