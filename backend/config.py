from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent
COUNTRIES = {
    "us": {"name": "United States", "language": "en", "flag": "🇺🇸"},
    "gb": {"name": "United Kingdom", "language": "en", "flag": "🇬🇧"},
    "fr": {"name": "France", "language": "fr", "flag": "🇫🇷"},
    "de": {"name": "Germany", "language": "de", "flag": "🇩🇪"},
    "jp": {"name": "Japan", "language": "ja", "flag": "🇯🇵"},
    "in": {"name": "India", "language": "hi", "flag": "🇮🇳"},
}
LANGUAGES = {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "hi": "हिन्दी",
    "ja": "日本語",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    groq_api_key: str = Field(default="", repr=False)
    elevenlabs_api_key: str = Field(default="", repr=False)
    news_api_key: str = Field(default="", repr=False)
    newsdata_api_key: str = Field(default="", repr=False)
    news_provider: str = "gnews"
    groq_model: str = "openai/gpt-oss-120b"
    cache_dir: Path = ROOT / "data/cache"
    audio_dir: Path = ROOT / "data/audio"


settings = Settings()
