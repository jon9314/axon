# Setup Guide

Install dependencies with Poetry:

```bash
poetry install
```

Optional features are grouped as extras:

```bash
poetry install --with calendar,postgres,vector,notify
```

On first run Axon will copy `config/settings.example.yaml` to
`config/settings.yaml` if the file is missing.
