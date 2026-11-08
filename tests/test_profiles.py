import unittest

import yaml

from scripts.update_profiles import convert_ini, parse_group, parse_rule_target, validate_output


class ProfileConversionTests(unittest.TestCase):
    def test_group_filter_and_references(self):
        group = parse_group(
            "Media`select`[]Proxy`(HK|Hong Kong)`(TW|Taiwan)", 1
        )
        self.assertEqual(group["proxies"], ["Proxy"])
        self.assertTrue(group["include-all-proxies"])
        self.assertEqual(group["filter"], "(?:HK|Hong Kong)|(?:TW|Taiwan)")

    def test_url_test_options(self):
        group = parse_group(
            "Japan`url-test`(JP|Japan)`https://example.com/ping`300,,125", 1
        )
        self.assertEqual(group["type"], "url-test")
        self.assertEqual(group["url"], "https://example.com/ping")
        self.assertEqual(group["interval"], 300)
        self.assertEqual(group["tolerance"], 125)

    def test_ini_to_routing_fragment(self):
        source = b"""[custom]
custom_proxy_group=Proxy`select`[]HK
custom_proxy_group=HK`select`(HK|Hong Kong)
ruleset=Proxy,https://example.com/proxy.list
ruleset=HK,[]GEOIP,CN
ruleset=Proxy,[]FINAL
"""
        generated = convert_ini(source, 1)
        content = validate_output(generated)
        parsed = yaml.safe_load(content)
        provider = next(iter(parsed["rule-providers"]))
        self.assertEqual(parsed["rules"], [
            f"RULE-SET,{provider},Proxy",
            "GEOIP,CN,HK",
            "MATCH,Proxy",
        ])
        self.assertEqual(parsed["proxy-groups"][1]["filter"], "(?:HK|Hong Kong)")

    def test_clash_classic_provider_is_yaml(self):
        providers = {}
        rules = []
        parse_rule_target(
            "Media",
            "clash-classic:https://example.com/provider.yaml",
            providers,
            rules,
        )
        provider = next(iter(providers.values()))
        self.assertEqual(provider["format"], "yaml")
        self.assertEqual(provider["behavior"], "classical")
        self.assertTrue(rules[0].endswith(",Media"))


if __name__ == "__main__":
    unittest.main()
