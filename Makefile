AWS_PROFILE=$(shell yq -er '.awsProfile' config.yaml)

deploy: build-react
	cdk deploy static-high-side-site --profile ${AWS_PROFILE} --require-approval never
destroy:
	cdk destroy static-high-side-site --profile ${AWS_PROFILE} --force
build-react:
	cd react-app && yarn build

# You'll be prompted for your sudo password (if on mac)
pre-commit:
	hookspath=$(shell git config core.hooksPath); \
	sudo git config --system --unset-all core.hooksPath; \
	pre-commit install; \
	sudo git config --system core.hooksPath "$$hookspath"
