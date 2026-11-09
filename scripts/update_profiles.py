#!/usr/bin/env python3
"""Convert SubConverter remoteConfig presets into 3x-ui routing fragments."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PAGE = (
    "https://raw.githubusercontent.com/youshandefeiyang/"
    "sub-web-modify/master/src/views/Subconverter.vue"
)
REPO_RAW = "https://raw.githubusercontent.com/Murphy08/clash-rules/main"
MIN_PROFILE_COUNT = 50
MAX_SOURCE_BYTES = 4_000_000
MAX_OUTPUT_BYTES = 2_000_000
EXCLUDED_PATH = ROOT / "config" / "excluded_404.json"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Murphy08-clash-rules/1.0"})
    with urllib.request.urlopen(request, timeout=40) as response:
        data = response.read(MAX_SOURCE_BYTES + 1)
    if not data or len(data) > MAX_SOURCE_BYTES:
        raise ValueError(f"source is empty or too large: {url}")
    return data


def get_catalog() -> list[dict[str, str]]:
    text = fetch(SOURCE_PAGE).decode("utf-8")
    start = text.find("remoteConfig: [")
    end = text.find("      form: {", start)
    if start < 0 or end < 0:
        raise ValueError("could not locate remoteConfig in upstream Subconverter.vue")
    block = text[start:end]
    pattern = re.compile(
        r'label:\s*"(?P<label>[^"]+)"\s*,\s*value:\s*"(?P<url>[^"]+)"',
        re.DOTALL,
    )
    entries = [
        {"name": match.group("label"), "url": match.group("url")}
        for match in pattern.finditer(block)
    ]
    if len(entries) < MIN_PROFILE_COUNT:
        raise ValueError(f"remoteConfig catalog unexpectedly small: {len(entries)}")
    excluded = {
        item["url"]
        for item in json.loads(EXCLUDED_PATH.read_text(encoding="utf-8"))
    }
    return [entry for entry in entries if entry["url"] not in excluded]


def slug(index: int, name: str) -> str:
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10]
    return f"profile-{digest}"


def provider_name(index: int, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"rule_{digest}"


def split_ini_line(line: str, key: str) -> str | None:
    prefix = key + "="
    return line[len(prefix) :].strip() if line.startswith(prefix) else None


def parse_group(value: str, index: int) -> dict:
    fields = value.split("`")
    if len(fields) < 2:
        raise ValueError(f"invalid custom_proxy_group: {value}")
    name, kind = fields[:2]
    kind_map = {"select": "select", "url-test": "url-test", "fallback": "fallback", "load-balance": "load-balance"}
    if kind not in kind_map or not name:
        raise ValueError(f"unsupported proxy group: {value}")
    group: dict = {"name": name, "type": kind_map[kind]}
    if kind != "select":
        group["url"] = "https://www.gstatic.com/generate_204"
        group["interval"] = 300
    references: list[str] = []
    filters: list[str] = []
    trailing_options = False
    for field in fields[2:]:
        field = field.strip()
        if not field:
            continue
        if trailing_options:
            values = field.split(",")
            if values[0].strip().isdigit():
                group["interval"] = int(values[0].strip())
            if len(values) > 2 and values[2].strip().isdigit():
                group["tolerance"] = int(values[2].strip())
            trailing_options = False
            continue
        if field.startswith("[]"):
            references.append(field[2:])
        elif field.startswith("(") and field.endswith(")"):
            filters.append(field[1:-1])
        elif field.startswith("^") or field == ".*":
            filters.append(field)
        elif field.startswith("http://") or field.startswith("https://"):
            group["url"] = field
            trailing_options = True
        elif re.fullmatch(r"\d+", field):
            group["interval"] = int(field)
        elif field == "" or field == ",":
            continue
        elif field.startswith("!!GROUP"):
            filters.append(".*")
        else:
            filters.append(re.escape(field))
    if filters:
        group["include-all-proxies"] = True
        group["filter"] = "|".join(f"(?:{item})" for item in filters)
    if references:
        group["proxies"] = list(dict.fromkeys(references))
    if not references and not filters:
        raise ValueError(f"group has no node selector: {value}")
    return group


def parse_rule_target(destination: str, value: str, providers: dict, rules: list[str]) -> None:
    if value.startswith("[]"):
        rule = value[2:]
        parts = rule.split(",")
        if parts[0] in {"FINAL", "MATCH"}:
            if len(parts) > 3:
                raise ValueError(f"invalid final rule: {value}")
            rules.append(f"MATCH,{destination}")
            return
        if parts[0] in {"GEOIP", "IP-CIDR", "IP-CIDR6", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"} and len(parts) >= 2:
            options = [part for part in parts[2:] if part]
            if any(option != "no-resolve" for option in options):
                raise ValueError(f"unsupported inline rule option: {value}")
            suffix = ",no-resolve" if "no-resolve" in options else ""
            rules.append(f"{parts[0]},{parts[1]},{destination}{suffix}")
            return
        raise ValueError(f"unsupported inline rule: {value}")
    behavior, format_name = "classical", "text"
    source_match = re.fullmatch(r"(clash-[a-z]+):(https?://.+)", value)
    if source_match:
        format_name = "yaml"
        behavior = {
            "clash-classic": "classical",
            "clash-ipcidr": "ipcidr",
            "clash-domain": "domain",
        }.get(source_match.group(1), "")
        if not behavior:
            raise ValueError(f"unsupported rule source format: {source_match.group(1)}")
        url = source_match.group(2)
    else:
        url = value
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError(f"invalid rule source URL: {value}")
    name = provider_name(len(providers) + 1, url)
    if name not in providers:
        providers[name] = {
            "type": "http",
            "behavior": behavior,
            "format": format_name,
            "url": url,
            "path": f"./rule_providers/{name}.{'yaml' if format_name == 'yaml' else 'list'}",
            "interval": 86400,
        }
    rules.append(f"RULE-SET,{name},{destination}")


def convert_ini(raw: bytes, profile_index: int) -> dict:
    text = raw.decode("utf-8-sig")
    groups: list[dict] = []
    group_index: dict[str, int] = {}
    provider_definitions: dict[str, dict] = {}
    rules: list[str] = []
    pending: list[tuple[str, str]] = []
    imports: list[str] = []
    group_imports: list[str] = []
    rule_base: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith((";", "#")):
            continue
        if line.startswith("clash_rule_base="):
            rule_base = line.split("=", 1)[1].strip()
            continue
        group_value = split_ini_line(line, "custom_proxy_group")
        if group_value is not None:
            if group_value.startswith("!!import:"):
                group_imports.append(group_value.removeprefix("!!import:"))
                continue
            group = parse_group(group_value, profile_index)
            if group["name"] in group_index:
                raise ValueError(f"duplicate proxy group {group['name']}")
            group_index[group["name"]] = len(groups)
            groups.append(group)
            continue
        rule_value = split_ini_line(line, "ruleset") or split_ini_line(line, "surge_ruleset")
        if rule_value is not None:
            if rule_value.startswith("!!import:"):
                imports.append(rule_value.removeprefix("!!import:"))
                continue
            fields = rule_value.split(",", 1)
            if len(fields) != 2 or not fields[0].strip():
                raise ValueError(f"invalid ruleset entry: {line}")
            pending.append((fields[0].strip(), fields[1].strip()))
    for import_url in group_imports:
        imported = fetch(import_url).decode("utf-8-sig")
        for imported_line in imported.splitlines():
            imported_line = imported_line.strip()
            if not imported_line or imported_line.startswith((";", "#")):
                continue
            if imported_line.startswith("custom_proxy_group="):
                imported_line = imported_line.split("=", 1)[1]
            group = parse_group(imported_line, profile_index)
            if group["name"] not in group_index:
                group_index[group["name"]] = len(groups)
                groups.append(group)
    if not groups and rule_base:
        base = convert_yaml(fetch(rule_base))
        groups = base["proxy-groups"]
        provider_definitions.update(base.get("rule-providers", {}))
    for import_url in imports:
        imported = fetch(import_url).decode("utf-8-sig")
        for imported_line in imported.splitlines():
            imported_line = imported_line.strip()
            if not imported_line or imported_line.startswith((";", "#")):
                continue
            fields = imported_line.split(",", 1)
            if len(fields) != 2:
                raise ValueError(f"invalid imported ruleset: {imported_line}")
            pending.append((fields[0].strip(), fields[1].strip()))
    if not groups or not pending:
        raise ValueError("INI profile must define proxy groups and rulesets")
    for destination, source in pending:
        parse_rule_target(destination, source, provider_definitions, rules)
    existing_names = {group["name"] for group in groups}
    missing_refs = {
        ref
        for group in groups
        for ref in group.get("proxies", [])
        if ref not in existing_names | {"DIRECT", "REJECT"}
    }
    for ref in sorted(missing_refs):
        if ref == "REJECT-TINYGIF":
            groups.append({"name": ref, "type": "select", "proxies": ["REJECT"]})
            existing_names.add(ref)
        else:
            raise ValueError(f"proxy group references unknown group {ref}")
    destinations = {rule.rsplit(",", 1)[-1] for rule in rules}
    for destination in sorted(destinations - existing_names - {"DIRECT", "REJECT"}):
        groups.append({"name": destination, "type": "select", "include-all-proxies": True})
    names = {group["name"] for group in groups}
    names.update({"DIRECT", "REJECT"})
    for group in groups:
        for reference in group.get("proxies", []):
            if reference not in names:
                raise ValueError(f"{group['name']} references unknown group {reference}")
    for rule in rules:
        target = rule.rsplit(",", 1)[-1]
        if target not in names:
            raise ValueError(f"rule references unknown group {target}")
    return {"proxy-groups": groups, "rule-providers": provider_definitions, "rules": rules}


def convert_yaml(raw: bytes) -> dict:
    if b"{{" in raw or b"{%" in raw:
        raise ValueError("source is a SubConverter template, not standalone YAML")
    value = yaml.safe_load(raw)
    if not isinstance(value, dict):
        raise ValueError("YAML source must contain a mapping")
    custom = value.get("custom")
    if isinstance(custom, dict) and custom.get("clash_rule_base"):
        return convert_yaml(fetch(custom["clash_rule_base"]))
    allowed = ("proxy-groups", "rule-providers", "rules")
    result = {key: value[key] for key in allowed if key in value}
    if "proxy-groups" not in result or "rules" not in result:
        raise ValueError("YAML profile must contain proxy-groups and rules")
    return result


def validate_output(profile: dict) -> bytes:
    if not isinstance(profile.get("proxy-groups"), list) or not profile["proxy-groups"]:
        raise ValueError("output has no proxy-groups")
    names = {item.get("name") for item in profile["proxy-groups"] if isinstance(item, dict)}
    if None in names or len(names) != len(profile["proxy-groups"]):
        raise ValueError("output has invalid or duplicate proxy group names")
    providers = profile.get("rule-providers", {})
    if not isinstance(providers, dict):
        raise ValueError("rule-providers must be a mapping")
    for rule in profile.get("rules", []):
        parts = rule.split(",") if isinstance(rule, str) else []
        if not parts:
            raise ValueError(f"invalid rule: {rule!r}")
        if parts[0] == "RULE-SET" and (len(parts) != 3 or parts[1] not in providers):
            raise ValueError(f"invalid rule-provider reference: {rule}")
        target = parts[-1]
        if target not in names | {"DIRECT", "REJECT"}:
            raise ValueError(f"rule target does not exist: {target}")
    data = yaml.safe_dump(profile, allow_unicode=True, sort_keys=False).encode("utf-8")
    if len(data) > MAX_OUTPUT_BYTES:
        raise ValueError("generated routing fragment exceeds 2 MiB")
    return data


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    entries = get_catalog()
    excluded = json.loads(EXCLUDED_PATH.read_text(encoding="utf-8"))
    (ROOT / "dist").mkdir(exist_ok=True)
    output_rows = []
    failures = []
    for index, entry in enumerate(entries, 1):
        key = slug(index, entry["name"])
        target = ROOT / "dist" / f"{key}.yaml"
        try:
            raw = fetch(entry["url"])
            if entry["url"].lower().endswith((".yaml", ".yml")):
                profile = convert_yaml(raw)
            else:
                profile = convert_ini(raw, index)
            content = validate_output(profile)
            target.write_bytes(content)
            output_rows.append((entry["name"], f"{REPO_RAW}/dist/{key}.yaml"))
            print(f"OK {key}: {entry['name']}")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                excluded.append({"name": entry["name"], "url": entry["url"]})
                if target.exists():
                    target.unlink()
                failures.append({"index": key, "name": entry["name"], "url": entry["url"], "error": "HTTP 404; excluded from sync"})
                print(f"EXCLUDE {key}: {entry['name']} (HTTP 404)")
                continue
            failures.append({"index": key, "name": entry["name"], "url": entry["url"], "error": str(exc)})
            if target.exists():
                output_rows.append((entry["name"], f"{REPO_RAW}/dist/{key}.yaml"))
                print(f"KEEP {key}: {entry['name']} ({exc})")
            else:
                print(f"FAIL {key}: {entry['name']} ({exc})")
        except Exception as exc:
            failures.append({"index": key, "name": entry["name"], "url": entry["url"], "error": str(exc)})
            if target.exists():
                output_rows.append((entry["name"], f"{REPO_RAW}/dist/{key}.yaml"))
                print(f"KEEP {key}: {entry['name']} ({exc})")
            else:
                print(f"FAIL {key}: {entry['name']} ({exc})")
    EXCLUDED_PATH.write_text(json.dumps(excluded, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {"profiles": len(entries), "updated_or_retained": len(output_rows), "failures": failures}
    report_path = ROOT / "reports" / "latest.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(output_rows)
    print(f"Updated {len(output_rows)} profiles; {len(failures)} sources failed or retained.")
    return 0


def write_readme(output_rows: list[tuple[str, str]], destination: Path | None = None) -> None:
    routing_url = f"{REPO_RAW}/dist/3x-ui.yaml"
    lines = [
        "# Clash routing fragments",
        "",
        "**3x-ui 基础路由（每天北京时间 00:00 直接同步 ACL4SSR）**",
        "",
        f"[{routing_url}]({routing_url})",
        "",
        "将此地址填入 3x-ui 的「全局路由规则 HTTPS URL」，保存后刷新面板订阅。保留「节点选择」「PROXY」「兜底选择」和内联规则，最后一条为 `MATCH,兜底选择`。",
        "",
        "参考 [kuchiki111/3x-ui-clash-ymal](https://github.com/kuchiki111/3x-ui-clash-ymal) 的生成逻辑，采用相同的规则源、顺序和三个策略组；每天直接下载 [ACL4SSR 源库](https://github.com/ACL4SSR/ACL4SSR/tree/master/Clash/Providers) 中的 `LocalAreaNetwork`、`UnBan`、`BanAD`、`BanProgramAD`、`ProxyGFWlist`、`ChinaDomain`、`ChinaIp`，展开为内联规则。规则和分组设置见 [本地策略](config/3x-ui-policy.yaml)，校验值见 [同步报告](reports/3x-ui.json)。",
        "",
        "「兜底选择」默认直连，也可切换为「节点选择」。实际节点由 3x-ui 提供；所有规则已内联，无需客户端下载远程规则提供者。下载或校验失败时保留最后有效文件。GitHub 定时任务可能延迟。",
        "",
        "## 分组配置（每周同步）",
        "",
        "Files are 3x-ui global routing fragments. They contain proxy groups, rule providers, and rules; node definitions and credentials remain in 3x-ui.",
        "",
        "The scheduled workflow runs every Monday at 00:00 China Standard Time. It refreshes the catalog from `sub-web-modify`; temporary non-404 failures keep their last valid generated file. Sources returning HTTP 404 are excluded from later runs.",
        "",
        "Only profiles converted and validated successfully are listed below. Unsupported templates and sources requiring authentication are omitted; details are in [the latest report](reports/latest.json).",
        "",
        "| Configuration | Raw YAML |",
        "| --- | --- |",
    ]
    lines.extend(f"| {name.replace('|', '\\|')} | [{url}]({url}) |" for name, url in output_rows)
    lines.extend(["", f"Source catalog: [sub-web-modify Subconverter.vue]({SOURCE_PAGE})", ""])
    (destination or ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
