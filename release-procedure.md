# Release Procedure for tide-sdk

This document outlines the step-by-step process for creating a new release of the tide-sdk package.

## Prerequisites

- Ensure you have push access to the repository
- Have `uv` installed locally
- Have git configured with your credentials
- All changes you want to include in the release should be merged to `main`

## Release Steps

### 1. Prepare the Release

1. **Switch to main branch and pull latest changes:**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Verify the build works locally:**
   ```bash
   uv sync
   uv run pytest
   ```

3. **Determine the new version number:**
   - Follow [Semantic Versioning](https://semver.org/)
   - `MAJOR.MINOR.PATCH` (e.g., 0.1.6 → 0.1.7 for patch, 0.1.6 → 0.2.0 for minor)
   - Current version can be found in `pyproject.toml`

### 2. Update Version Numbers

Update the version in **all** of the following files:

1. **`pyproject.toml`:**
   ```toml
   [project]
   name = "tide-sdk"
   version = "X.Y.Z"  # Update this line
   ```

2. **`tide/__init__.py`:**
   ```python
   __version__ = "X.Y.Z"  # Update this line
   ```

3. **`setup.py`:**
   ```python
   version="X.Y.Z",  # Update this line
   ```



### 3. Commit and Create Release

1. **Commit the version changes:**
   ```bash
   git add pyproject.toml tide/__init__.py setup.py
   git commit -m "Bump version to X.Y.Z"
   ```

2. **Push the commit:**
   ```bash
   git push origin main
   ```

3. **Create and push the git tag:**
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

   **Note:** The tag must start with 'v' (e.g., `v0.1.7`) to trigger the GitHub Action.

### 5. Monitor the Release

1. **Check the GitHub Action:**
   - Go to the [Actions tab](https://github.com/your-repo/actions) on GitHub
   - Verify the "Publish Python package" workflow is running/completed successfully

2. **Verify the package on PyPI:**
   - Check [PyPI](https://pypi.org/project/tide-sdk/) to confirm the new version is available
   - This may take a few minutes after the workflow completes

### 6. Test the Published Package

1. **Test installation from PyPI:**
   ```bash
   # In a fresh environment
   pip install tide-sdk==X.Y.Z
   python -c "import tide; print(tide.__version__)"
   ```

## Troubleshooting

### If the GitHub Action fails:
1. Check the action logs for specific error messages
2. Common issues:
   - Version conflicts (version already exists on PyPI)
   - Build errors (missing dependencies, test failures)
   - Authentication issues with PyPI

### If you need to fix issues after tagging:
1. **Delete the tag locally and remotely:**
   ```bash
   git tag -d vX.Y.Z
   git push origin :refs/tags/vX.Y.Z
   ```

2. **Fix the issues, commit, and repeat the process**

### If the package exists on PyPI but has issues:
- You cannot overwrite a version on PyPI
- You must increment the version number (e.g., 0.1.7 → 0.1.8)
- Consider it a patch release with the fixes

## Release Checklist

- [ ] Updated version in `pyproject.toml`
- [ ] Updated version in `tide/__init__.py`
- [ ] Updated version in `setup.py`
- [ ] Tested locally with `uv run pytest`
- [ ] Verified version with `uv run tide --version`
- [ ] Committed version changes
- [ ] Pushed commit to main
- [ ] Created and pushed git tag (vX.Y.Z)
- [ ] Verified GitHub Action completed successfully
- [ ] Confirmed new version is available on PyPI
- [ ] Tested installation from PyPI

## Notes

- The GitHub Action automatically handles the build and publish process
- The action uses OpenID Connect (OIDC) for PyPI authentication, so no manual credentials are needed
- The package is built as both source distribution (sdist) and wheel
- Tags must follow the pattern `v*` (e.g., `v0.1.7`, `v1.0.0`) to trigger the release workflow 