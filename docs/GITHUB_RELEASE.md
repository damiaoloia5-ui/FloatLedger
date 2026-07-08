# GitHub Release Guide

This directory is prepared as a GitHub repository for DeepSeek Balance Monitor.

## Files to commit

Commit the source code, build scripts, documentation, and the curated installer copy under `releases/`.

Do not commit:

- `build/`
- `dist/`
- `output/`
- `__pycache__/`
- `.venv/`
- `snapshot.json`
- `.env` or any file containing a real DeepSeek API Key

## Suggested first commit

```powershell
git status
git add .
git commit -m "Initial release"
```

## Create a GitHub repository

If using GitHub CLI:

```powershell
gh repo create DeepSeekMonitor --public --source . --remote origin --push
```

If the repository already exists on GitHub:

```powershell
git remote add origin https://github.com/<your-user-or-org>/DeepSeekMonitor.git
git branch -M main
git push -u origin main
```

## Publish the installer

Recommended release tag: `v1.0.0`

With GitHub CLI:

```powershell
gh release create v1.0.0 releases/DeepSeekMonitor_Setup_1.0.0.exe --title "DeepSeek Monitor 1.0.0" --notes-file CHANGELOG.md
```

Or open the repository on GitHub, create a new Release, and upload `releases/DeepSeekMonitor_Setup_1.0.0.exe` manually.

## Final security check

Before pushing or creating a Release, scan again for real API keys and confirm that only placeholder text remains.
