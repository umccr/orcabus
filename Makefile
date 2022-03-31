install:
	pip install -r requirements.txt       # pulls in CDKv2 `aws-cdk-lib` and `construct` libs
	npm install -g aws-cdk

	brew tap aws/tap
	brew reinstall aws-sam-cli
build:
#   Build lambda Layer
	for dir in $(shell find ./lambdas/layers -maxdepth 1 -mindepth 1 -type d -exec basename {} \;); do ./lambdas/layers/create_layer_package.sh $$dir; done
#   Build Cdk to cdk.out
	cdk synth
deploy: build
	cdk deploy UmccrEventBus
	cdk deploy UmccrEventBusSchemaStack
run:
	sam local invoke
