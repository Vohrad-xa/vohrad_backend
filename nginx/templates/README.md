# Nginx Configuration Templates

This directory contains nginx configuration templates that use environment variable substitution.

## Files

- `production.conf` - Production nginx configuration template with `${DOMAIN}` placeholders

## Usage

During deployment, the deploy script processes templates and outputs them to `nginx/conf.d/`:

```bash
envsubst '${DOMAIN}' < nginx/templates/production.conf > nginx/conf.d/default.conf
```

The processed files in `nginx/conf.d/` are ignored by git and created during deployment.
