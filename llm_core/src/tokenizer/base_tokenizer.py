from abc import ABC, abstractmethod


class BaseTokenizer(ABC):
    @abstractmethod
    def encode(self, text: str):
        pass

    @abstractmethod
    def decode(self, text: str):
        pass

    @abstractmethod
    def save(self, path: str):
        pass

    @abstractmethod
    def load(self, path: str):
        pass