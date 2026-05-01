import json
from pathlib import Path
from typing import Any

from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel

from utils.file import rd

base_path = Path(__file__).parent.parent / "prompts"
base_path = base_path.resolve()


def serialize_parameter(param: Any, indent: int = None) -> str:
    def contains_pydantic(obj: Any) -> bool:
        """Check if object contains any Pydantic models."""
        if isinstance(obj, BaseModel):
            return True
        if isinstance(obj, list | tuple):
            return any(contains_pydantic(item) for item in obj)
        if isinstance(obj, dict):
            return any(contains_pydantic(v) for v in obj.values())
        return False

    def convert_to_dict(obj: Any) -> Any:
        """Recursively convert Pydantic models to dicts."""
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if isinstance(obj, list | tuple):
            return [convert_to_dict(item) for item in obj]
        if isinstance(obj, dict):
            return {k: convert_to_dict(v) for k, v in obj.items()}
        return obj

    if contains_pydantic(param):
        param = convert_to_dict(param)

    return json.dumps(param, indent=indent, default=str, ensure_ascii=False)


def prompt(module: str, code: str, typ: str, **kwargs) -> str:
    txt = rd(base_path / f"{module}.{code}.{typ}.md")
    for k, v in kwargs.items():
        txt = txt.replace(f"{{{k}}}", serialize_parameter(v))
    return txt


def sprompt(module: str, code: str, **kwargs) -> str:
    return prompt(module, code, "system", **kwargs)


def uprompt(module: str, code: str, **kwargs) -> str:
    return prompt(module, code, "user", **kwargs)


def tprompt(module: str, code: str, **kwargs) -> PromptTemplate:
    txt = rd(base_path / f"{module}.{code}.md")
    st = txt.find("\n")
    var_names = json.loads(txt[:st])
    txt = txt[st:]
    # for k, v in kwargs.items():
    #     txt =
    return PromptTemplate(
        template=txt,
        input_variables=var_names,
        partial_variables=kwargs,
    )
