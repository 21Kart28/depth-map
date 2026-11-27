"""The fixed list of themes an analysis may pick from, loaded from data/codebook.json."""

import json
from importlib import resources

from depthmap.models import Code

GROUPS = {"interpersonal", "avoidance", "repetitive-thinking", "functioning", "change", "positive"}
REQUIRED_TEXT = ("definition", "example", "counter_example")


class Codebook:
    def __init__(self, version: str, codes: list[Code]):
        self.version = version
        self.codes = codes
        self._by_id = {code.id: code for code in codes}

    def get(self, code_id: str) -> Code | None:
        return self._by_id.get(code_id)

    def active_ids(self) -> list[str]:
        # every code is active until codes can be retired
        return [code.id for code in self.codes]


def parse_codebook(data: dict) -> Codebook:
    """Check the shape of a codebook and build it, naming the code that is wrong."""
    codes = []
    seen = set()
    for item in data["codes"]:
        code_id = item["id"]
        if code_id in seen:
            raise ValueError(f"code {code_id}: duplicate id")
        seen.add(code_id)
        if item.get("group") not in GROUPS:
            raise ValueError(f"code {code_id}: unknown group {item.get('group')!r}")
        for field in REQUIRED_TEXT:
            if not item.get(field, "").strip():
                raise ValueError(f"code {code_id}: missing {field}")
        codes.append(Code(**item))
    return Codebook(data["version"], codes)


def load_codebook() -> Codebook:
    path = resources.files("depthmap") / "data" / "codebook.json"
    return parse_codebook(json.loads(path.read_text(encoding="utf-8")))
