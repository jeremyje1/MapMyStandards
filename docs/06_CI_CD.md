# 06 – GitHub Actions pipeline

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test-build-deploy:
    runs-on: ubuntu-latest
    services:
      postgres: {image: postgres:15, ports: ["5432:5432"], env: {POSTGRES_PASSWORD: a3e}}
      milvus:   {image: milvusdb/milvus:v2.4.0, ports: ["19530:19530"]}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest
      - uses: docker/login-action@v3
        with: {registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }}}
      - run: docker build -t ghcr.io/${{ github.repository }}:sha-${{ github.sha }} .
      - run: docker push ghcr.io/${{ github.repository }}:sha-${{ github.sha }}
      - uses: aws-actions/amazon-ecr-login@v1
      - run: |
          aws ecs update-service \
            --cluster a3e-prod \
            --service api \
            --force-new-deployment
```
