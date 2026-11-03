import ast, importlib.util, json, logging, pathlib, re, unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[2]

class ObservabilityAssetTests(unittest.TestCase):
    def test_dashboards_are_valid_json_without_secrets(self):
        directory = ROOT / "monitoring/grafana"
        files = sorted(
            path for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() == ".json"
        )
        self.assertGreaterEqual(len(files), 5)
        for path in files:
            with self.subTest(path=path.relative_to(ROOT)):
                data = json.loads(path.read_text(encoding="utf-8"))
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

if __name__=="__main__": unittest.main()
