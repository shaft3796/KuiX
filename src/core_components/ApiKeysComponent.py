import json
import os

from BaseCoreComponent import BaseCoreComponent
from src.core.Exceptions import GenericException


class KeysDecodingException(GenericException):
    pass


class ApiKeysComponent(BaseCoreComponent):

    def __init__(self, core, path: str = None):
        """
        Handles the API keys.
        :param core: core instance.
        :param path: Default path is Kuix/keys.json, use this to override the default path.

        :raises KeysDecodingException: If the keys.json file is corrupted.
        """
        super().__init__(core)
        self.path = path
        if self.path is None:
            self.path = self.core.root_path + "keys.json"

        self.keys = {"JSON_KEY_EXAMPLE": ["API_KEY_EXAMPLE", "API_SECRET_EXAMPLE"]}

        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)
            with open(self.path, "w") as f:
                json.dump(self.keys, f, indent=4)

        try:
            with open(self.path, "r") as f:
                self.keys = json.load(f)
        except Exception as e:
            raise KeysDecodingException(f"Failed to decode keys.json file.") + e

    def get_value(self, json_key: str):
        """
        Get the value of a json key.
        :param json_key: Json key name.
        :return: the value of the key.

        :raises KeyError: If the key is not found.
        """
        return self.keys[json_key]
