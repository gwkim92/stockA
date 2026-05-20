from __future__ import annotations

from pathlib import Path


def resolve_repo_root(repo_root: str | Path | None) -> Path:
    if repo_root is None:
        return Path.cwd().resolve()
    return Path(repo_root).expanduser().resolve()


def resolve_existing_file(
    value: str | Path,
    *,
    label: str,
    repo_root: str | Path | None = None,
    require_repo_outside: bool = False,
) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    if require_repo_outside:
        ensure_repo_outside(path, repo_root=repo_root, label=label)
    return path


def resolve_output_path(
    value: str | Path,
    *,
    label: str,
    repo_root: str | Path | None = None,
    require_repo_outside: bool = False,
    create_parent: bool = True,
) -> Path:
    path = Path(value).expanduser().resolve()
    if require_repo_outside:
        ensure_repo_outside(path, repo_root=repo_root, label=label)
    if create_parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def ensure_repo_outside(
    path: str | Path,
    *,
    repo_root: str | Path | None,
    label: str,
) -> Path:
    resolved_path = Path(path).expanduser().resolve()
    root = resolve_repo_root(repo_root)
    if resolved_path == root or resolved_path.is_relative_to(root):
        raise ValueError(f"{label} must be outside repository: {resolved_path}")
    return resolved_path
