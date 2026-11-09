import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import yaml

from scripts.update_profiles import write_readme
from scripts.update_routing_only import convert, update


class RoutingOnlyTests(unittest.TestCase):
    def test_preserves_route_order_and_no_resolve_without_groups(self):
        source = {
            "proxy-groups": [{"name": "PROXY", "type": "select", "proxies": ["vpn"]}],
            "proxies": [{"name": "vpn", "type": "socks5", "server": "example.com", "port": 1080}],
            "rules": [
                "DOMAIN-SUFFIX,lan,DIRECT",
                "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve",
                "IP-CIDR6,fc00::/7,DIRECT,no-resolve",
                "DOMAIN-SUFFIX,example.com,PROXY",
                "DOMAIN-SUFFIX,ads.example,REJECT",
                "GEOIP,CN,DIRECT,no-resolve",
                "MATCH,兜底选择",
            ],
        }
        result = yaml.safe_load(convert(yaml.safe_dump(source).encode("utf-8")))
        self.assertEqual(set(result), {"rules"})
        self.assertEqual(result["rules"], source["rules"][:-1] + ["MATCH,DIRECT"])

    def test_rejects_unknown_targets_missing_fallback_and_misplaced_options(self):
        for rules in (
            ["DOMAIN-SUFFIX,example.com,unknown", "MATCH,DIRECT"],
            ["DOMAIN-SUFFIX,example.com,DIRECT"],
            ["MATCH,DIRECT", "MATCH,PROXY"],
            ["GEOIP,CN,no-resolve,DIRECT", "MATCH,DIRECT"],
            ["IP-CIDR,fc00::/7,DIRECT", "MATCH,DIRECT"],
            ["RULE-SET,external,DIRECT", "MATCH,DIRECT"],
        ):
            with self.subTest(rules=rules), self.assertRaises(ValueError):
                convert(yaml.safe_dump({"rules": rules}).encode("utf-8"))

    def test_failed_download_preserves_last_valid_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "dist/routing-only.yaml"
            output.parent.mkdir()
            output.write_bytes(b"rules:\n- MATCH,DIRECT\n")
            with patch("scripts.update_routing_only.urllib.request.urlopen", side_effect=URLError("offline")):
                with self.assertRaises(URLError):
                    update(root)
            self.assertEqual(output.read_bytes(), b"rules:\n- MATCH,DIRECT\n")

    def test_weekly_readme_regeneration_keeps_daily_link_first(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "README.md"
            weekly_url = "https://example.com/grouped.yaml"
            write_readme([("Grouped", weekly_url)], output)
            content = output.read_text(encoding="utf-8")
            self.assertLess(content.index("/dist/routing-only.yaml"), content.index(weekly_url))
            self.assertIn("每天北京时间 00:00", content)


if __name__ == "__main__":
    unittest.main()
