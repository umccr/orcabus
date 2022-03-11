build:
#   Build lambda Layer
	for dir in $(shell find ./lambdas/layers -maxdepth 1 -mindepth 1 -type d -exec basename {} \;); do ./lambdas/layers/create_layer_package.sh $$dir; done
#   Build Cdk to cdk.out
	cdk synth
deploy: build
	cdk deploy UmccrEventBus --profile ${AWS_PROFILE}
	cdk deploy UmccrEventBusSchemaStack --profile ${AWS_PROFILE}
run:
	sam local invoke
