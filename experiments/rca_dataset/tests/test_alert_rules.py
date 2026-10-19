import requests

from tripsphere_rca.runner import alert_rules


def test_activate_alert_rules_replaces_active_file_and_reloads_prometheus(
    tmp_path, monkeypatch
):
    source = tmp_path / "selected.yaml"
    source.write_text("groups: []\n", encoding="utf-8")
    active = tmp_path / "active.yaml"
    monkeypatch.setattr(alert_rules, "ACTIVE_RULES_PATH", active)

    calls = []

    def fake_post(url, timeout):
        calls.append((url, timeout))
        response = requests.Response()
        response.status_code = 200
        return response

    monkeypatch.setattr(alert_rules.requests, "post", fake_post)
    selected = alert_rules.activate_alert_rules(source, "http://prometheus:9090")

    assert selected == source
    assert active.read_text(encoding="utf-8") == "groups: []\n"
    assert calls == [("http://prometheus:9090/-/reload", 5)]
