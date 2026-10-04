"""Load lesson identifiers from generated content"""

import json
from pathlib import Path


def load_lesson_slugs(manifest_path: str) -> set[str]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))

    return {lesson["slug"] for module in manifest["modules"] for lesson in module["lessons"]}
