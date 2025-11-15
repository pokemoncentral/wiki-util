import dataclasses
import json
from dataclasses import dataclass
from typing import Any, Optional, Self


@dataclass(kw_only=True)
class AltForms:
    # ndex: int
    key: str = dataclasses.field(init=False)

    anchor: Optional[str] = None
    blacklinks: dict[str, str]
    cries: Optional[list[str]] = None
    ext: dict[str, str]
    gamesOrder: dict[str, str]
    links: dict[str, str]
    names: dict[str, str]
    plainlinks: dict[str, str]
    since: dict[str, str]
    until: Optional[str] = None

    @property
    def base_name(self) -> str:
        return self.names["base"]

    def add_key(self, key: str):
        self.key = key
        base_name = self.names["base"]
        if base_name == "":
            self.names["base"] = self.key.capitalize()

    @classmethod
    def from_json(cls, file_path: str) -> dict[str, Self]:
        with open(file_path, "r") as f:
            lua_export = json.load(f, object_hook=cls._json_object_hook)

        alt_form_items = {
            name: form_data
            for name, form_data in lua_export.items()
            if isinstance(form_data, cls) and not is_int(name)
        }

        for key, form_data in alt_form_items.items():
            form_data.add_key(key)

        return alt_form_items

    @classmethod
    def _json_object_hook(cls, json_dict: dict[str, Any]) -> Self | dict[str, Any]:
        if set(json_dict.keys()) >= cls.init_field_names:
            return cls(**json_dict)
        return json_dict


AltForms.init_field_names = {
    f.name
    for f in dataclasses.fields(AltForms)
    if f.init and f.default == dataclasses.MISSING
}


def is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False
