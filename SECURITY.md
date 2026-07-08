# Security Policy

## API Key handling

This repository and its release installer must not include a real DeepSeek API Key.

The application asks each user to enter their own API Key on first launch. The key is stored only on that user's machine at `%APPDATA%\DeepSeekMonitor\snapshot.json`.

Before publishing, verify that these files are not committed:

- `snapshot.json`
- `.env` or `.env.*`
- logs or screenshots containing a real `sk-...` key
- any local AppData copy of `DeepSeekMonitor`

## Release checklist

1. Rebuild the executable and installer from a clean working tree.
2. Confirm no `snapshot.json` exists inside `dist/`, `output/`, or `releases/`.
3. Scan the repository for real DeepSeek key patterns.
4. Upload the installer through GitHub Releases.

## Reporting security issues

If you find a security issue, do not open a public issue containing secrets. Contact the project maintainer privately and include only the minimum details needed to reproduce the problem.
