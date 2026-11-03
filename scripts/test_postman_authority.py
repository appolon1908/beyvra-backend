"""Derived requests must target their own OpenAPI server paths."""
import json
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'Beyvra-Enterprise-Experience': 'contracts/openapi/beyvra-enterprise-experience-v1.yaml',
    'Beyvra-Financial-Service': 'contracts/financial-service/v1/openapi.yaml',
    'Beyvra-Treasury': 'contracts/openapi/beyvra-treasury-v1.yaml',
    'Beyvra-Core-Trading-API': 'contracts/openapi/beyvra-openapi-3.1.yaml',
    'Beyvra-Codestra-Real-Wallet': 'contracts/openapi/codestra-real-wallet-v1.yaml',
    'Beyvra-Workspace': 'contracts/openapi/beyvra-workspace-v1.yaml',
}


def requests(items):
    for item in items:
        if 'request' in item:
            yield item['request']
        yield from requests(item.get('item', []))


class PostmanAuthorityTests(unittest.TestCase):
    def test_server_prefixes_match_openapi_route_authorities(self):
        from urllib.parse import urlsplit
        methods = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'}
        for name, source in SOURCES.items():
            with self.subTest(collection=name):
                document = yaml.safe_load((ROOT / source).read_text())
                expected = set()
                for path, path_item in document['paths'].items():
                    for method, operation in path_item.items():
                        if method not in methods:
                            continue
                        servers = operation.get('servers', path_item.get('servers', document.get('servers', [{'url': ''}])))
                        prefix = urlsplit(servers[0]['url']).path.rstrip('/')
                        expected.add((method.upper(), prefix + path))
                collection = json.loads((ROOT / 'postman' / (name + '.postman_collection.json')).read_text())
                actual = []
                for request in requests(collection['item']):
                    raw = request['url']['raw']
                    self.assertTrue(raw.startswith('{{base_url}}/'))
                    path = raw.removeprefix('{{base_url}}').split('?', 1)[0]
                    path = re.sub(r'\{\{([A-Za-z_][A-Za-z_0-9]*)\}\}', r'{\1}', path)
                    actual.append((request['method'], path))
                self.assertEqual(set(actual), expected)
                self.assertEqual(len(actual), len(expected))

    def test_openapi_path_parameters_are_postman_variables(self):
        for name in SOURCES:
            collection = json.loads((ROOT / 'postman' / (name + '.postman_collection.json')).read_text())
            for request in requests(collection['item']):
                with self.subTest(collection=name, url=request['url']['raw']):
                    without_variables = re.sub(r'\{\{[^{}]+\}\}', '', request['url']['raw'])
                    self.assertNotRegex(without_variables, r'[{}]')

    def test_default_targets_and_credentials_remain_local_and_empty(self):
        from urllib.parse import urlsplit
        for name in SOURCES:
            collection = json.loads((ROOT / 'postman' / (name + '.postman_collection.json')).read_text())
            variables = {item['key']: item['value'] for item in collection['variable']}
            with self.subTest(collection=name):
                self.assertEqual(urlsplit(variables['base_url']).hostname, '127.0.0.1')
                for key in ('bearer_token', 'beyvra_access'):
                    if key in variables:
                        self.assertEqual(variables[key], '')

    def test_enterprise_collection_uses_its_cookie_security_contract(self):
        name = 'Beyvra-Enterprise-Experience.postman_collection.json'
        collection = json.loads((ROOT / 'postman' / name).read_text())
        for request in requests(collection['item']):
            headers = {header['key'].lower(): header['value'] for header in request['header']}
            self.assertEqual(headers.get('cookie'), 'beyvra_access={{beyvra_access}}')
            self.assertNotIn('authorization', headers)
