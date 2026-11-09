#!/usr/bin/env python3
"""Mirror upstream inline routing rules without defining proxy groups."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "https://raw.githubusercontent.com/kuchiki111/3x-ui-clash-ymal/main/dist/3x-ui.yaml"
MAX_BYTES = 2 * 1024 * 1024
TARGETS = {"DIRECT", "REJECT", "PROXY"}
VALUE_RULES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-WILDCARD", "DOMAIN-KEYWORD",
    "IP-CIDR", "IP-CIDR6", "GEOIP",
}
IP_RULES = {"IP-CIDR", "IP-CIDR6"}


def convert(raw: bytes) -> bytes:
    source = yaml.safe_load(raw)
    if not isinstance(source, dict) or not isinstance(source.get("rules"), list):
        raise ValueError("upstream must contain a rules list")
    source_rules = source["rules"]
    if not source_rules:
        raise ValueError("upstream rules list is empty")
    result = []
    for index, rule in enumerate(source_rules):
        if not isinstance(rule, str):
            raise ValueError(f"rule {index}: expected a string")
        parts = [part.strip() for part in rule.split(",")]
        if any(not part for part in parts):
            raise ValueError(f"rule {index}: empty rule parameter")
        kind = parts[0]
        if kind == "MATCH":
            if len(parts) != 2 or index != len(source_rules) - 1:
                raise ValueError("MATCH must occur once, at the end")
            target_index = 1
        elif kind in VALUE_RULES:
            if len(parts) == 4:
                if kind not in IP_RULES | {"GEOIP"} or parts[3] != "no-resolve":
                    raise ValueError(f"rule {index}: unsupported rule option")
            elif len(parts) != 3:
                raise ValueError(f"rule {index}: invalid parameter count")
            target_index = 2
            if kind in IP_RULES:
                network = ipaddress.ip_network(parts[1], strict=False)
                if (kind == "IP-CIDR6") != (network.version == 6):
                    raise ValueError(f"rule {index}: IP version does not match rule type")
        else:
            raise ValueError(f"rule {index}: unsupported inline rule type {kind}")
        target = parts[target_index]
        # The upstream fallback selector defaults to DIRECT. PROXY is supplied by 3x-ui.
        if target == "兜底选择":
            target = "DIRECT"
        if target not in TARGETS:
            raise ValueError(f"rule {index}: unknown route target {target}")
        parts[target_index] = target
        result.append(",".join(parts))
    if not result[-1].startswith("MATCH,"):
        raise ValueError("last rule must be MATCH")
    content = yaml.safe_dump({"rules": result}, allow_unicode=True, sort_keys=False).encode("utf-8")
    if len(content) > MAX_BYTES:
        raise ValueError("routing output exceeds the 3x-ui limit of 2 MiB")
    return content


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".routing-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def update(root: Path = ROOT) -> None:
    request = urllib.request.Request(UPSTREAM, headers={"User-Agent": "Murphy08-clash-rules/1.0"})
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read(MAX_BYTES + 1)
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("upstream YAML is empty or larger than 2 MiB")
    content = convert(raw)
    rules = yaml.safe_load(content)["rules"]
    report = {
        "source": UPSTREAM,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "output": "dist/routing-only.yaml",
        "rule_count": len(rules),
        "route_counts": {
            target: sum(rule.split(",")[1 if rule.startswith("MATCH,") else 2] == target for rule in rules)
            for target in sorted(TARGETS)
        },
        "fallback": "DIRECT",
    }
    atomic_write(root / "dist/routing-only.yaml", content)
    atomic_write(
        root / "reports/routing-only.json",
        (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    print(f"Updated dist/routing-only.yaml: {len(rules)} inline rules; no proxy groups")


def main() -> int:
    try:
        update()
    except Exception as exc:
        print(f"Routing sync failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
