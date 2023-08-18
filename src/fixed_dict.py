from typing import Any
from collections.abc import Mapping
    

class FixedDict(dict):   
    """
    A dictionary that can only contain a fixed set of keys
    """   
    def __init__(self, keys: list[str], *args, **kwargs) -> None:
        super().__init__()
        self.__allowed_keys = keys
        copy = dict(*args, **kwargs)
        self.update(copy)

    def __setitem__(self, key: str, value: Any) -> None:
        if key not in self.__allowed_keys:
            raise KeyError(key)
        return super().__setitem__(key, value)

    def update(self, other=None, **kwargs) -> None:
        if other is not None:
            for k, v in other.items() if isinstance(other, Mapping) else other:
                self[k] = v
        for k, v in kwargs.items():
            self[k] = v