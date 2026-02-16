# SME Release Strategy (v2.0.0)

For a multi-service application like SME (Operator, Sidecar, Frontend), the following release strategy is recommended for professional deployment:

## Release Impact & SME Specifics

| Strategy Component | Impact for SME | Recommendation |
| :--- | :--- | :--- |
| **Git Tagging** | Creates an "Audit Trail" for forensic logic. | Use Annotated Tags (`-a`) exactly as planned. Gold standard for version control. |
| **GitHub Release** | Provides a visual "Changelog" for the Control Room UI. | Attach `docker-compose.yaml` as a Release Asset for one-click deployment. |
| **GHCR (Docker)** | Critical. Bypasses Win32 errors via OS isolation. | Tag images by service (operator, sidecar, frontend) to optimize footprint. |
| **PyPI** | Good for the `sme-core` library. | **Wait.** Prioritize Docker images for the "Control Room" experience. |

---

## 1. Git Tagging (The Foundation)

Tagging creates a permanent marker in your history for this version, establishing a forensic audit trail for the logic implemented.

- **Command**: `git tag -a v2.0.0 -m "Release v2.0.0: The Control Room"`
- **Push**: `git push origin v2.0.0`

## 2. GitHub Release (The User Portal)

Once tagged, use the GitHub UI to create a "Release":

1. Go to **Releases** > **Draft a new release**.
2. Select tag **v2.0.0**.
3. Use the "Generate release notes" button to automate the changelog.
4. **Asset Attachment**: Manually upload your `docker-compose.yaml` to the release. This allows users to deploy the entire stack with a single file.

## 3. GitHub Container Registry (GHCR) - *Critical for SME*

Since SME interacts with complex dependencies (R, Python 3.14, GPU drivers), pushing your images to GHCR is the **only way** to bypass local Win32/versioning errors for end-users.

```bash
docker pull ghcr.io/spectredeath/sme-operator:v2.0.0
```

- **Status**: CI/CD Automation is already implemented to push to GHCR on every tag.
- **Optimization**: Images are tagged by service to keep the pull times fast.

## 4. PyPI (Python Package Index)

If you want others to `pip install sme-forensic-toolkit`:

1. **Requirements**: A clean `pyproject.toml` (already updated).
2. **Action**: `python -m build` and `python -m twine upload dist/*`.

> [!NOTE]
> Since SME is a multi-service application, the Docker images are significantly more important for a working "Control Room" experience than a partial PyPI package.

## Immediate Path Taken

1. [x] **Tag the release**: v2.0.0 created with annotated metadata.
2. [ ] **Create the GitHub Release**: (Manual step on GitHub) - *Upload docker-compose.yaml here.*
3. [x] **Automate Docker Builds**: CI workflow updated to push to GHCR.

---

## ⚠️ Final Release Checklist (Action Required)

Since the `v2.0.0` tag is pushed and the CI/CD is in motion, perform these final checks:

1. **Actions Status**: Check the **Actions** tab on GitHub to ensure the `SME Forensic Lab CI` workflow didn't fail on the docker push step.
2. **Package Visibility**: By default, **GHCR packages** are often private. Go to Package Settings on GitHub and ensure they are set to **Public** if you want them accessible via a simple `docker pull`.
3. **Asset Manual Step**: Don't forget to **manually upload** the `docker-compose.yaml` to the GitHub Release page so users have the "blueprint" to connect all three containers.
