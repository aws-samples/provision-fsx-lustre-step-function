# Define make entry and help functionality
.DEFAULT_GOAL := help

.PHONY: help

init: ## Initialize the project for running with CDK.
	@poetry install

bootstrap: ## Bootstrap the AWS account to support CDK deployments 
	@poetry run cdk bootstrap

synth: ## Synthesize the CloudFormation Stack Template from the CDK
	@poetry run cdk synth

deploy: ## Deploy the CloudFormation Stack to the AWS account
	@poetry run cdk deploy

teardown: ## Destroy the CloudFormation Stack to the AWS account
	@poetry run cdk destroy

test: ## Run pytest against the project.
	@TESTING=1 AWS_DEFAULT_REGION="us-east-1" poetry run pytest -v --cov-config=.coveragerc --cov=provision_fsx_lustre_step_function/ tests/unit/test_*.py

update-deps: ## Update the package dependencies via Poetry.
	@poetry update

bandit-baseline: ## Create the Bandit baseline file.
	@poetry run bandit -f yaml -o .bandit-baseline.yml -c "pyproject.toml" -r .

help: ## Show this help information.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-25s\033[0m %s\n", $$1, $$2}'
