build:
	@rm -rf asset
	@mkdir -p asset
	@yarn run build-src
	@cd dist && zip -r ../asset/src.zip .

	@mkdir -p nodejs
	@cp -r node_modules ./nodejs
	@zip -r asset/dependency.zip nodejs
	@rm -rf nodejs
