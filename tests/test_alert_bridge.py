from alert_bridge import RadioAlertBridge


def test_backend_endpoint_normalization(monkeypatch):
    monkeypatch.setenv("PLAYER_ALERT_DIRECT_BACKEND_URL", "https://example.invalid")
    bridge = RadioAlertBridge()
    assert bridge._backend_endpoint("send") == "https://example.invalid/api/player-alert/send"


def test_message_summary_has_no_secret(monkeypatch):
    monkeypatch.setenv("PLAYER_ALERT_WORKER_TOKEN", "super-secret-value")
    bridge = RadioAlertBridge()
    assert "super-secret-value" not in bridge.masked_summary()
