import ast, importlib.util, json, logging, pathlib, re, unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[2]


def _dashboard_object(pairs):
    """Reject ambiguous JSON objects before any values can be overwritten."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate dashboard key: {key}")
        result[key] = value
    return result

class ObservabilityAssetTests(unittest.TestCase):
    def test_dashboards_are_valid_json_without_secrets(self):
        files = sorted(
            path
            for directory in ("monitoring/grafana", "observability/grafana")
            for path in (ROOT / directory).rglob("*")
            if path.is_file() and path.suffix.lower() == ".json"
        )
        self.assertGreaterEqual(len(files), 10)
        for path in files:
            with self.subTest(path=path.relative_to(ROOT)):
                data = json.loads(
                    path.read_text(encoding="utf-8"), object_pairs_hook=_dashboard_object
                )
                self.assertTrue(data["title"])
                self.assertTrue(data["panels"])
                # Scan decoded keys and values, including JSON unicode escapes.
                text = json.dumps(data, ensure_ascii=False).lower()
                self.assertNotRegex(
                    text, r"password|api[_-]?key|authorization|jwt|private[_-]?key"
                )
    def test_metric_names_are_canonical_and_labels_bounded(self):
        text=(ROOT/"FX/apps/foundation/observability.py").read_text()
        names=set(re.findall(r'["\'](beyvra_[a-z0-9_]+)["\']',text)); self.assertGreaterEqual(len(names),45)
        forbidden={"user_id","order_id","trade_id","request_id","correlation_id","email","account_id","container_id","pid","url","channel"}
        tree=ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node,(ast.Call,)):
                for arg in node.args[2:]:
                    if isinstance(arg,(ast.Tuple,ast.List)):
                        labels={x.value for x in arg.elts if isinstance(x,ast.Constant) and isinstance(x.value,str)}
                        self.assertFalse(labels & forbidden)
    def test_alerts_have_severity_runbook_and_sustained_noisy_conditions(self):
        text=(ROOT/"monitoring/prometheus/beyvra-alerts.yml").read_text()
        alerts=re.split(r"\n  - alert: ",text)[1:]; self.assertGreaterEqual(len(alerts),10)
        for alert in alerts:
            self.assertRegex(alert,r"severity: (info|warning|critical)"); self.assertIn("runbook:",alert)
        self.assertNotIn('status_class=~"4',text)
    def test_public_proxy_does_not_expose_internal_monitoring(self):
        nginx=(ROOT/"nginx/nginx.prod.conf.template").read_text().lower()
        for path in ("/metrics","/prometheus/","/grafana/"):
            self.assertRegex(nginx,rf"location[^{{]*{re.escape(path)}[^{{]*{{\s*return 404;")
    def test_health_response_has_no_topology_or_secrets(self):
        text=(ROOT/"FX/apps/foundation/health.py").read_text().lower()
        self.assertNotRegex(text,r"\b(password|token|credential|hostname|port)\b")
        self.assertIn('def live(',text); self.assertIn('def ready(',text)
    def test_structured_logger_redacts_secret_values(self):
        path=ROOT/"FX/fx_utils/json_logging.py"; spec=importlib.util.spec_from_file_location("json_logging",path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        record=logging.LogRecord("test",logging.INFO,"",0,"token=supersecret event ok",(),None); data=json.loads(module.JsonFormatter().format(record))
        self.assertNotIn("supersecret",json.dumps(data)); self.assertEqual(data["service"],"beyvra-backend"); self.assertIn("environment",data); self.assertIn("simulation",data)


class DashboardScanRegressionTests(unittest.TestCase):
    def _write_valid_dashboards(self, root):
        directory = root / "monitoring/grafana"
        directory.mkdir(parents=True)
        for index in range(5):
            (directory / f"beyvra-{index}.json").write_text(
                json.dumps({"title": f"Dashboard {index}", "panels": [{"id": 1}]}),
                encoding="utf-8",
            )
        other = root / "observability/grafana"
        other.mkdir(parents=True)
        for index in range(5):
            (other / f"other-{index}.json").write_text(
                json.dumps({"title": f"Other {index}", "panels": [{"id": 1}]}),
                encoding="utf-8",
            )
        return directory

    def _scan(self, root):
        with patch(__name__ + ".ROOT", root):
            ObservabilityAssetTests(
                "test_dashboards_are_valid_json_without_secrets"
            ).test_dashboards_are_valid_json_without_secrets()

    def test_additional_dashboard_name_and_uppercase_suffix_are_scanned(self):
        with TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            directory = self._write_valid_dashboards(root)
            (directory / "operator.JSON").write_text(
                '{"title": "operator", "panels": [{"password": "fixture"}]}',
                encoding="utf-8",
            )
            with self.assertRaises(AssertionError):
                self._scan(root)

    def test_escaped_secret_key_is_detected_after_json_decoding(self):
        with TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            directory = self._write_valid_dashboards(root)
            (directory / "beyvra-escaped.json").write_text(
                r'{"title": "operator", "panels": [{"api\u005fkey": "fixture"}]}',
                encoding="utf-8",
            )
            with self.assertRaises(AssertionError):
                self._scan(root)

    def test_escaped_secret_value_is_detected_after_json_decoding(self):
        with TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            directory = self._write_valid_dashboards(root)
            (directory / "beyvra-escaped.json").write_text(
                r'{"title": "operator", "panels": [{"expr": "api\u002dkey=fixture"}]}',
                encoding="utf-8",
            )
            with self.assertRaises(AssertionError):
                self._scan(root)

    def test_additional_clean_dashboards_do_not_disable_existing_checks(self):
        with TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            directory = self._write_valid_dashboards(root)
            (directory / "operator.JSON").write_text(
                '{"title": "operator", "panels": [{"id": 1}]}',
                encoding="utf-8",
            )
            self._scan(root)

<<<<<<< HEAD
    def test_nested_dashboard_in_either_root_is_scanned(self):
        for directory_name in ("monitoring/grafana", "observability/grafana"):
            with self.subTest(directory=directory_name), TemporaryDirectory() as temporary:
                root = pathlib.Path(temporary)
                self._write_valid_dashboards(root)
                nested = root / directory_name / "nested"
                nested.mkdir()
                (nested / "operator.JSON").write_text(
                    r'{"title": "nested", "panels": [{"private\u005fkey": "fixture"}]}',
                    encoding="utf-8",
                )
                with self.assertRaises(AssertionError):
                    self._scan(root)

    def test_clean_nested_dashboards_in_both_roots_are_accepted(self):
        with TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            self._write_valid_dashboards(root)
            for directory_name in ("monitoring/grafana", "observability/grafana"):
                nested = root / directory_name / "nested"
                nested.mkdir()
                (nested / "operator.JSON").write_text(
                    '{"title": "nested", "panels": [{"id": 1}]}',
                    encoding="utf-8",
                )
            self._scan(root)
=======
    def test_duplicate_json_key_cannot_hide_escaped_secret_value(self):
        with TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            directory = self._write_valid_dashboards(root)
            (directory / "beyvra-duplicate.json").write_text(
                r'{"title": "operator", "panels": [{"expr": "api\u005fkey=fixture", "expr": "safe"}]}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate dashboard key"):
                self._scan(root)
>>>>>>> repair/pr128

if __name__=="__main__": unittest.main()
