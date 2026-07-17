from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import shutil
from pathlib import Path


LICENSE_PREFIXES = ("license", "copying", "notice", "authors")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "package"


def license_files(distribution: importlib.metadata.Distribution) -> list[Path]:
    matches: set[Path] = set()
    for relative in distribution.files or []:
        if any(part.lower().startswith(LICENSE_PREFIXES) for part in relative.parts):
            source = Path(distribution.locate_file(relative))
            if source.is_file():
                matches.add(source)
    return sorted(matches)


def copy_distribution(
    distribution: importlib.metadata.Distribution,
    output_dir: Path,
) -> dict[str, object]:
    name = distribution.metadata.get("Name") or "unknown"
    version = distribution.version or "unknown"
    target = output_dir / f"{safe_name(name)}-{safe_name(version)}"
    copied: list[str] = []
    for index, source in enumerate(license_files(distribution), start=1):
        target.mkdir(parents=True, exist_ok=True)
        destination = target / f"{index:02d}-{safe_name(source.name)}"
        shutil.copy2(source, destination)
        copied.append(destination.relative_to(output_dir).as_posix())
    return {
        "name": name,
        "version": version,
        "license": distribution.metadata.get("License", ""),
        "homepage": distribution.metadata.get("Home-page", ""),
        "files": copied,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = [
        copy_distribution(distribution, args.out)
        for distribution in importlib.metadata.distributions()
    ]
    manifest.sort(key=lambda item: str(item["name"]).lower())
    output = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (args.out / "manifest.json").write_text(output, encoding="utf-8")
    print(f"Collected license metadata for {len(manifest)} Python distributions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
