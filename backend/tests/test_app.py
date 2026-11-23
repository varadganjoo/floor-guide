from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


def test_health_response_exposes_only_service_status():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": app.title}


def test_settings_load_dotenv_and_mask_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("APP_NAME", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=test-secret\nAPP_NAME=Test API\nUNRELATED_SETTING=value\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.app_name == "Test API"
    assert settings.openai_api_key.get_secret_value() == "test-secret"
    assert "test-secret" not in repr(settings)


def test_environment_overrides_dotenv(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=File value\n", encoding="utf-8")
    monkeypatch.setenv("APP_NAME", "Environment value")

    assert Settings(_env_file=env_file).app_name == "Environment value"
