import json
import os

from BaseStrategyComponent import BaseStrategyComponent


class PersistenceComponent(BaseStrategyComponent):
    def __init__(self, worker, name: str = "${STRATEGY_NAME}_${WORKER_ID}", root_path: str = None):
        """
        Instance a persistence component to save persistent data to disk as json.
        :param worker: Worker instance, pass 'self' from the worker constructor.
        :param name: Name of the storage folder, use ${STRATEGY_NAME} and ${WORKER_ID} to insert the strategy name and
        the worker id. Default is ${STRATEGY_NAME}_${WORKER_ID}.
        :param root_path: Storage folder is defaulted to KuiX storage, use this to override the default path.
        """
        super().__init__(worker)

        self.name = name.replace("${STRATEGY_NAME}", self.worker.strategy.__class__.__name__) \
            .replace("${WORKER_ID}", self.worker.identifier)

        self.root_path = root_path
        if self.root_path is None:
            self.root_path = self.worker.process.root_path + f"components/persistence/{self.name}/"
        os.makedirs(self.root_path, exist_ok=True)

        self.data = {}

    def load(self):
        """
        Load the json file
        :return: the loaded data as a dictionary.
        """
        if not os.path.exists(self.root_path + "data.json"):
            with open(self.root_path + "data.json", "w") as f:
                json.dump(self.data, f, indent=4)
        with open(self.root_path + "data.json", "r") as f:
            self.data = json.load(f)
        return self.data

    def save(self):
        """
        Save the json file
        :return: None
        """
        with open(self.root_path + "data.json", "w") as f:
            json.dump(self.data, f, indent=4)
