from pathlib import Path
from typing import Dict, Any, Optional

import dotenv
from pydantic import BaseModel, AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, YamlConfigSettingsSource


class LLMCreds(BaseModel):
    url: str
    token: str
    model: str
    provider: str
    props: Dict[str, Any]
    type: str = "chat"

class LLMConfig(BaseModel):
    provider: str
    model: str
    type: str = "chat"
    props: Dict[str, Any] = Field(default_factory=dict)


class LLMProvider(BaseModel):
    url: AnyUrl
    token: str


class DocumentConfig(BaseModel):
    pass

class S3Config(BaseModel):
    url: str
    key_id: str
    access_key: str
    bucket: str

class N4JConfig(BaseModel):
    conn: str
    url: str
    username: str
    password: str

class RedisConfig(BaseModel):
    conn: str

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
    s3: Optional[S3Config] = None
    n4j: N4JConfig
    redis: RedisConfig

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
