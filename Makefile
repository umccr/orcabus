build:
	sam-beta-cdk build
deploy: build
	cdk deploy -a .aws-sam/build --profile dev
run:
	sam-beta-cdk local invoke
