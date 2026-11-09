import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import yaml

from scripts.sync_3x_ui import UPSTREAM, build, update
from scripts.update_profiles import write_readme


def fixture():
    return {
        "providers": {
            "LocalAreaNetwork": {"behavior": "classical", "min_entries": 1},
            "ProxyGFWlist": {"behavior": "classical", "min_entries": 1},
            "ChinaIp": {"behavior": "ipcidr", "min_entries": 1},
        },
        "proxy-groups": [
            {"name": "节点选择", "type": "select", "include-all-proxies": True, "proxies": []},
            {"name": "PROXY", "type": "select", "hidden": True, "proxies": ["节点选择"]},
            {"name": "兜底选择", "type": "select", "proxies": ["DIRECT", "节点选择"]},
        ],
        "custom_rules": ["DOMAIN-SUFFIX,internal.example,DIRECT"],
        "rules": [
            "RULE-SET,LocalAreaNetwork,DIRECT",
            "RULE-SET,ProxyGFWlist,PROXY",
            "RULE-SET,ChinaIp,DIRECT",
            "GEOIP,CN,DIRECT",
            "MATCH,兜底选择",
        ],
    }, {
        "LocalAreaNetwork": ["IP-CIDR,10.0.0.0/8,no-resolve"],
        "ProxyGFWlist": ["DOMAIN-SUFFIX,*.example.com"],
        "ChinaIp": ["1.0.1.0/24", "fc00::/7"],
    }


class ACL4SSRTests(unittest.TestCase):
    def test_build_preserves_groups_fallback_and_rule_order(self):
        policy, sources = fixture()
        generated = yaml.safe_load(build(policy, sources))
        self.assertEqual(set(generated), {"proxy-groups", "rules"})
        self.assertEqual(generated["proxy-groups"], policy["proxy-groups"])
        self.assertEqual(generated["rules"], [
            "DOMAIN-SUFFIX,internal.example,DIRECT",
            "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
            "DOMAIN-WILDCARD,*.example.com,PROXY",
            "IP-CIDR,1.0.1.0/24,DIRECT",
            "IP-CIDR6,fc00::/7,DIRECT",
            "GEOIP,CN,DIRECT",
            "MATCH,兜底选择",
        ])

    def test_rejects_unknown_target_and_insufficient_rules(self):
        policy, sources = fixture()
        unknown = copy.deepcopy(policy)
        unknown["rules"][0] = "RULE-SET,LocalAreaNetwork,unknown"
        with self.assertRaises(ValueError):
            build(unknown, sources)
        insufficient = copy.deepcopy(policy)
        insufficient["providers"]["LocalAreaNetwork"]["min_entries"] = 2
        with self.assertRaises(ValueError):
            build(insufficient, sources)

    def test_update_reads_acl4ssr_providers_and_writes_report(self):
        policy, sources = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config/3x-ui-policy.yaml").write_text(yaml.safe_dump(policy), encoding="utf-8")
            with patch("scripts.sync_3x_ui.read_provider", side_effect=lambda name: yaml.safe_dump({"payload": sources[name]}).encode("utf-8")) as downloader:
                update(root)
            self.assertCountEqual([call.args[0] for call in downloader.call_args_list], list(sources))
            report = json.loads((root / "reports/3x-ui.json").read_text(encoding="utf-8"))
            self.assertEqual(report["final_rule"], "MATCH,兜底选择")
            self.assertEqual(report["mode"], "direct_acl4ssr_inline_build")
            self.assertTrue(all(item["url"].startswith(UPSTREAM) for item in report["providers"].values()))
            self.assertEqual(yaml.safe_load((root / "dist/3x-ui.yaml").read_bytes())["proxy-groups"], policy["proxy-groups"])

    def test_download_or_validation_failure_preserves_last_valid_output(self):
        policy, _ = fixture()
        for failure in (URLError("offline"), b"payload: []\n"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "config").mkdir()
                (root / "config/3x-ui-policy.yaml").write_text(yaml.safe_dump(policy), encoding="utf-8")
                output = root / "dist/3x-ui.yaml"
                output.parent.mkdir()
                previous = b"last valid output"
                output.write_bytes(previous)
                kwargs = {"side_effect": failure} if isinstance(failure, Exception) else {"return_value": failure}
                with patch("scripts.sync_3x_ui.read_provider", **kwargs), self.assertRaises((ValueError, URLError)):
                    update(root)
                self.assertEqual(output.read_bytes(), previous)

    def test_weekly_readme_regeneration_keeps_daily_link_first(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "README.md"
            weekly_url = "https://example.com/grouped.yaml"
            write_readme([("Grouped", weekly_url)], output)
            content = output.read_text(encoding="utf-8")
            self.assertLess(content.index("/dist/3x-ui.yaml"), content.index(weekly_url))
            self.assertIn("每天北京时间 00:00", content)
            self.assertIn("直接同步 ACL4SSR", content)
            self.assertIn("MATCH,兜底选择", content)


if __name__ == "__main__":
    unittest.main()
