# Development

## Set up

```bash
git clone https://github.com/GeiserX/slskd-transform.git
cd slskd-transform
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cp config.example.yml config.yml
# edit config.yml: host and api_key of your slskd
slskd-transform --help
```

`config.yml` is in `.gitignore`, so your key stays out of commits.

## Test

```bash
pytest tests/ --cov=src/slskd_transform --cov-report=term -v
```

The same command runs on every pull request and push to `main` as the `Tests` workflow, on Python 3.12, and uploads coverage to [Codecov](https://codecov.io/gh/GeiserX/slskd-transform). The tests mock slskd, so they need no running instance.

## Release

1. Bump the version in `pyproject.toml` and in `src/slskd_transform/__init__.py`.
2. Push to `main`, then push a new tag `vX.Y.Z`. Never move an existing tag.
3. Create the GitHub release from the tag, with the changes in its notes. Nothing is published to a registry: people install from the tag with `pip install git+https://github.com/GeiserX/slskd-transform.git@vX.Y.Z`.

## Docs

The site is built by MkDocs from `docs/`:

```bash
pip install -r docs/requirements-docs.txt
mkdocs build --strict
```

The same strict build runs on every pull request, and a push to `main` that touches the docs deploys the site.
