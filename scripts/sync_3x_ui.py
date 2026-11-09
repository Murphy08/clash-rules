#!/usr/bin/env python3
"""Build 3x-ui inline routing YAML directly from ACL4SSR provider files."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Providers/"
MAX_BYTES = 2 * 1024 * 1024
MAX_SOURCE_BYTES = 8_000_000
VALUE_RULES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-WILDCARD", "DOMAIN-KEYWORD",
    "IP-CIDR", "IP-CIDR6", "GEOIP",
}
IP_RULES = {"IP-CIDR", "IP-CIDR6"}


def validate(raw: bytes) -> dict:
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("upstream YAML is empty or larger than 2 MiB")
    source = yaml.safe_load(raw)
    if not isinstance(source, dict):
        raise ValueError("upstream must be a YAML mapping")
    groups, rules = source.get("proxy-groups"), source.get("rules")
    if not isinstance(groups, list) or not groups or not isinstance(rules, list) or not rules:
        raise ValueError("upstream must contain nonempty proxy-groups and rules lists")
    names = set()
    for group in groups:
        name = group.get("name") if isinstance(group, dict) else None
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("upstream contains invalid or duplicate group names")
        names.add(name)
    targets = names | {"DIRECT", "REJECT"}
    for group in groups:
        refs = group.get("proxies", [])
        if not isinstance(refs, list) or any(not isinstance(ref, str) or ref not in targets for ref in refs):
            raise ValueError("upstream group references an unknown group or node")
    for index, rule in enumerate(rules):
        if not isinstance(rule, str):
            raise ValueError(f"rule {index}: expected a string")
        parts = [part.strip() for part in rule.split(",")]
        if any(not part for part in parts):
            raise ValueError(f"rule {index}: empty rule parameter")
        kind = parts[0]
        if kind == "MATCH":
            if len(parts) != 2 or index != len(rules) - 1:
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
        if parts[target_index] not in targets:
            raise ValueError(f"rule {index}: unknown route target {parts[target_index]}")
    if not rules[-1].startswith("MATCH,"):
        raise ValueError("last rule must be MATCH")
    return source


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


def read_provider(name: str) -> bytes:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
        raise ValueError(f"invalid provider name: {name}")
    request = urllib.request.Request(
        f"{UPSTREAM}{name}.yaml", headers={"User-Agent": "Murphy08-clash-rules/1.0"}
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read(MAX_SOURCE_BYTES + 1)
    if not raw or len(raw) > MAX_SOURCE_BYTES:
        raise ValueError(f"{name}: provider file is empty or larger than 8 MB")
    return raw


def expand_entry(entry: str, behavior: str, target: str) -> str:
    if not isinstance(entry, str) or not entry.strip() or len(entry) > 2048:
        raise ValueError("provider entry must be a nonempty rule string")
    if behavior == "ipcidr":
        network = ipaddress.ip_network(entry, strict=False)
        kind = "IP-CIDR6" if network.version == 6 else "IP-CIDR"
        return f"{kind},{entry},{target}"
    if behavior != "classical":
        raise ValueError(f"unsupported provider behavior: {behavior}")
    parts = entry.split(",")
    if len(parts) not in (2, 3) or parts[0] not in VALUE_RULES - {"GEOIP"} or not parts[1]:
        raise ValueError(f"invalid classical provider entry: {entry}")
    if len(parts) == 3 and (parts[0] not in IP_RULES or parts[2] != "no-resolve"):
        raise ValueError(f"unsupported provider option: {entry}")
    kind = parts[0]
    if kind == "DOMAIN-SUFFIX" and parts[1].startswith("*."):
        kind = "DOMAIN-WILDCARD"
    suffix = ",no-resolve" if len(parts) == 3 else ""
    return f"{kind},{parts[1]},{target}{suffix}"


def build(policy: dict, sources: dict[str, list[str]]) -> bytes:
    if not isinstance(policy, dict) or not isinstance(policy.get("providers"), dict) or not policy["providers"]:
        raise ValueError("policy must contain a nonempty providers mapping")
    providers = policy["providers"]
    for name, spec in providers.items():
        if not isinstance(spec, dict) or spec.get("behavior") not in {"classical", "ipcidr"}:
            raise ValueError(f"{name}: unsupported provider specification")
        minimum = spec.get("min_entries")
        if type(minimum) is not int or minimum < 1:
            raise ValueError(f"{name}: invalid minimum rule count")
        entries = sources.get(name)
        if not isinstance(entries, list) or len(entries) < minimum:
            raise ValueError(f"{name}: provider has fewer than {minimum} rules")
    rules, custom = policy.get("rules"), policy.get("custom_rules", [])
    if not isinstance(rules, list) or not isinstance(custom, list):
        raise ValueError("policy rules and custom_rules must be lists")
    expanded = []
    for rule in custom + rules:
        if not isinstance(rule, str):
            raise ValueError("policy rule must be a string")
        parts = rule.split(",")
        if parts[0] == "RULE-SET":
            if len(parts) != 3 or parts[1] not in providers:
                raise ValueError(f"invalid policy provider reference: {rule}")
            name, target = parts[1:]
            expanded.extend(
                expand_entry(entry, providers[name]["behavior"], target)
                for entry in sources[name]
            )
        else:
            expanded.append(rule)
    document = {"proxy-groups": policy.get("proxy-groups"), "rules": expanded}
    content = yaml.safe_dump(document, allow_unicode=True, sort_keys=False).encode("utf-8")
    validate(content)
    return content


def update(root: Path = ROOT) -> None:
    policy_path = root / "config/3x-ui-policy.yaml"
    policy_raw = policy_path.read_bytes()
    policy = yaml.safe_load(policy_raw)
    if not isinstance(policy, dict) or not isinstance(policy.get("providers"), dict):
        raise ValueError("policy must contain a providers mapping")
    sources, details = {}, {}
    for name in policy["providers"]:
        raw = read_provider(name)
        provider = yaml.safe_load(raw)
        if not isinstance(provider, dict) or not isinstance(provider.get("payload"), list):
            raise ValueError(f"{name}: provider must contain a payload list")
        sources[name] = provider["payload"]
        details[name] = {
            "url": f"{UPSTREAM}{name}.yaml",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "entries": len(sources[name]),
        }
    content = build(policy, sources)
    source = yaml.safe_load(content)
    report = {
        "source": "https://github.com/ACL4SSR/ACL4SSR",
        "policy": "config/3x-ui-policy.yaml",
        "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "providers": details,
        "output_sha256": hashlib.sha256(content).hexdigest(),
        "output": "dist/3x-ui.yaml",
        "rule_count": len(source["rules"]),
        "proxy_groups": [group["name"] for group in source["proxy-groups"]],
        "final_rule": source["rules"][-1],
        "mode": "direct_acl4ssr_inline_build",
    }
    atomic_write(root / "dist/3x-ui.yaml", content)
    atomic_write(
        root / "reports/3x-ui.json",
        (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    print(f"Built dist/3x-ui.yaml directly from ACL4SSR: {len(source['rules'])} rules")


def main() -> int:
    try:
        update()
    except Exception as exc:
        print(f"3x-ui sync failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
