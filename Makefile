format:
	black ./ && \
	isort ./
test:
	black \
		--check \
		./ && \
	isort \
		--check \
		./ && \
	flake8 \
		--max-line-length 88 \
		--extend-ignore E203 \
		--statistics \
		./ && \
	pytest \
		tests \
		--cov=src \
		--cov-report term-missing \
		--cov-config=.coveragerc \
		--verbose
release: format test
