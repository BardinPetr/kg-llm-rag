from pathlib import Path
from typing import Dict, Any

import dotenv
from pydantic import BaseModel, AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, YamlConfigSettingsSource


class LLMCreds(BaseModel):
    url: str
    token: str
    model: str
    props: Dict[str, Any]

class LLMConfig(BaseModel):
    provider: str
    model: str
    props: Dict[str, Any] = Field(default_factory=dict)


class LLMProvider(BaseModel):
    url: AnyUrl
    token: str


class DocumentConfig(BaseModel):
    pass


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_file=".env",
        env_file_encoding="utf-8",
        yaml_file=Path(__file__).parent.parent.parent / "config.yaml",
        yaml_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # document: DocumentConfig
    providers: Dict[str, LLMProvider]
    llms: Dict[str, LLMConfig]

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls),)


dotenv.load_dotenv()
sys_cfg = AppConfig()
