SHELL := /bin/bash

docker: css
	docker build -t bloggy .

test:
	pytest

css:
	npx tailwindcss -i ./bloggy/templates/main.css \
		-o ./bloggy/static/css/main.css --minify

covrun:
	coverage run -m pytest

cov: covrun
	coverage report

run:
	flask --app bloggy run --debug

install:
	pip install -e .

startddb:
	docker run --rm -d --name ddb -p 8000:8000 amazon/dynamodb-local

stopddb:
	docker stop ddb

killddb:
	docker kill ddb

createtable:
	AWS_ACCESS_KEY_ID=foo \
	AWS_SECRET_ACCESS_KEY=bar \
	aws dynamodb create-table \
		--endpoint-url http://localhost:8000 \
		--table-name Blog \
		--key-schema '[{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}]' \
		--attribute-definitions '[ { "AttributeName": "pk", "AttributeType": "S"}, { "AttributeName": "sk", "AttributeType": "S"}, { "AttributeName": "data", "AttributeType": "S" } ]' \
		--billing-mode PAY_PER_REQUEST \
		--global-secondary-indexes '[ { "IndexName": "GSI", "KeySchema": [{"AttributeName": "sk", "KeyType": "HASH"}, {"AttributeName": "data", "KeyType": "RANGE"}], "Projection": { "ProjectionType": "ALL"}  } ]'
