"""告警系统测试。"""

from unittest.mock import patch

import pytest


class TestAlertModels:
    def test_alert_rule_defaults(self):
        from datacore.alert import AlertRule, AlertSeverity
        rule = AlertRule(name="test", metric_key="api", metric_field="success_rate", operator="lt", threshold=90)
        assert rule.enabled is True
        assert rule.severity == AlertSeverity.WARNING
        assert rule.duration_seconds == 0

    def test_alert_event_defaults(self):
        from datacore.alert import AlertEvent, AlertSeverity, AlertStatus
        evt = AlertEvent(rule_name="test", severity=AlertSeverity.WARNING, message="test msg")
        assert evt.status == AlertStatus.ACTIVE
        assert evt.resolved_at is None


class TestAlertNotifiers:
    def test_log_notifier(self):
        from datacore.alert import LogNotifier, AlertEvent, AlertSeverity
        notifier = LogNotifier()
        evt = AlertEvent(rule_name="test", severity=AlertSeverity.INFO, message="test")
        notifier.send(evt)  # 不应抛异常

    def test_file_notifier(self, tmp_path):
        from datacore.alert import FileNotifier, AlertEvent, AlertSeverity
        log_file = tmp_path / "alerts.log"
        notifier = FileNotifier(str(log_file))
        evt = AlertEvent(rule_name="test", severity=AlertSeverity.WARNING, message="file test", triggered_at=1000.0)
        notifier.send(evt)
        content = log_file.read_text(encoding="utf-8")
        assert "test" in content
        assert "warning" in content

    def test_base_notifier_not_implemented(self):
        from datacore.alert import AlertNotifier, AlertEvent, AlertSeverity
        notifier = AlertNotifier()
        evt = AlertEvent(rule_name="test", severity=AlertSeverity.INFO, message="test")
        with pytest.raises(NotImplementedError):
            notifier.send(evt)

    def test_webhook_notifier_failure(self):
        from datacore.alert import WebhookNotifier, AlertEvent, AlertSeverity
        notifier = WebhookNotifier("http://example.com/hook")
        evt = AlertEvent(rule_name="test", severity=AlertSeverity.WARNING, message="webhook test", triggered_at=1000.0)
        with patch("httpx.Client", side_effect=RuntimeError("connection failed")):
            notifier.send(evt)  # 异常被捕获，不应抛出


class TestAlertEngine:
    def test_evaluate_triggers_alert(self):
        from datacore.alert import AlertEngine, AlertRule, AlertSeverity
        engine = AlertEngine()
        engine.add_rule(AlertRule(
            name="low_rate", metric_key="api", metric_field="success_rate",
            operator="lt", threshold=90.0, severity=AlertSeverity.WARNING,
        ))
        metrics = {"api": {"success_rate": 50.0, "calls": 100}}
        events = engine.evaluate(metrics)
        assert len(events) == 1
        assert events[0].rule_name == "low_rate"

    def test_no_trigger_when_ok(self):
        from datacore.alert import AlertEngine, AlertRule
        engine = AlertEngine()
        engine.add_rule(AlertRule(
            name="low_rate", metric_key="api", metric_field="success_rate",
            operator="lt", threshold=90.0,
        ))
        metrics = {"api": {"success_rate": 95.0, "calls": 100}}
        events = engine.evaluate(metrics)
        assert len(events) == 0

    def test_rule_disabled(self):
        from datacore.alert import AlertEngine, AlertRule
        engine = AlertEngine()
        engine.add_rule(AlertRule(
            name="disabled_rule", metric_key="api", metric_field="success_rate",
            operator="lt", threshold=90.0, enabled=False,
        ))
        events = engine.evaluate({"api": {"success_rate": 50.0}})
        assert len(events) == 0

    def test_duplicate_suppression(self):
        from datacore.alert import AlertEngine, AlertRule
        engine = AlertEngine()
        engine.add_rule(AlertRule(
            name="dup_test", metric_key="api", metric_field="success_rate",
            operator="lt", threshold=90.0,
        ))
        metrics = {"api": {"success_rate": 50.0}}
        events1 = engine.evaluate(metrics)
        events2 = engine.evaluate(metrics)  # 5分钟内不重复
        assert len(events1) == 1
        assert len(events2) == 0

    def test_auto_resolve(self):
        from datacore.alert import AlertEngine, AlertRule
        engine = AlertEngine()
        engine.add_rule(AlertRule(
            name="resolve_test", metric_key="api", metric_field="success_rate",
            operator="lt", threshold=90.0,
        ))
        engine.evaluate({"api": {"success_rate": 50.0}})
        engine.evaluate({"api": {"success_rate": 95.0}})  # 恢复
        active = engine.get_active_alerts()
        assert len(active) == 0

    def test_get_active_alerts(self):
        from datacore.alert import AlertEngine
        engine = AlertEngine()
        assert engine.get_active_alerts() == []

    def test_get_history(self):
        from datacore.alert import AlertEngine, AlertRule
        engine = AlertEngine()
        engine.add_rule(AlertRule(name="hist", metric_key="api", metric_field="success_rate", operator="lt", threshold=90.0))
        engine.evaluate({"api": {"success_rate": 50.0}})
        history = engine.get_history()
        assert len(history) == 1

    def test_acknowledge(self):
        from datacore.alert import AlertEngine, AlertRule
        engine = AlertEngine()
        engine.add_rule(AlertRule(name="ack", metric_key="api", metric_field="success_rate", operator="lt", threshold=90.0))
        engine.evaluate({"api": {"success_rate": 50.0}})
        assert engine.acknowledge("ack") is True
        assert engine.acknowledge("nonexistent") is False

    def test_operator_gt(self):
        from datacore.alert import AlertEngine, AlertRule
        engine = AlertEngine()
        engine.add_rule(AlertRule(name="gt_test", metric_key="api", metric_field="latency", operator="gt", threshold=5.0))
        events = engine.evaluate({"api": {"latency": 10.0}})
        assert len(events) == 1

    def test_operator_eq(self):
        from datacore.alert import AlertEngine, AlertRule
        engine = AlertEngine()
        engine.add_rule(AlertRule(name="eq_test", metric_key="api", metric_field="latency", operator="eq", threshold=5.0))
        events = engine.evaluate({"api": {"latency": 5.0}})
        assert len(events) == 1

    def test_evaluate_missing_metric_key(self):
        from datacore.alert import AlertEngine, AlertRule
        engine = AlertEngine()
        engine.add_rule(AlertRule(name="missing_key", metric_key="api", metric_field="success_rate", operator="lt", threshold=90.0))
        events = engine.evaluate({"other": {"success_rate": 50.0}})
        assert len(events) == 0

    def test_evaluate_missing_metric_field(self):
        from datacore.alert import AlertEngine, AlertRule
        engine = AlertEngine()
        engine.add_rule(AlertRule(name="missing_field", metric_key="api", metric_field="success_rate", operator="lt", threshold=90.0))
        events = engine.evaluate({"api": {"calls": 100}})
        assert len(events) == 0

    def test_notifier_send_exception_silenced(self):
        from datacore.alert import AlertEngine, AlertRule, AlertNotifier, AlertEvent

        class BrokenNotifier(AlertNotifier):
            def send(self, event: AlertEvent) -> None:
                raise RuntimeError("_notifier_boom")

        engine = AlertEngine()
        engine.add_rule(AlertRule(name="silent", metric_key="api", metric_field="success_rate", operator="lt", threshold=90.0))
        engine.add_notifier(BrokenNotifier())
        events = engine.evaluate({"api": {"success_rate": 50.0}})
        assert len(events) == 1

    def test_create_default_engine(self):
        from datacore.alert import create_default_engine
        engine = create_default_engine()
        assert len(engine.rules) == 3
        assert len(engine.notifiers) >= 1

    def test_get_alert_engine_singleton(self):
        from datacore.alert import get_alert_engine
        e1 = get_alert_engine()
        e2 = get_alert_engine()
        assert e1 is e2
