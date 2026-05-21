from abc import ABC, abstractmethod


class Tool(ABC):
    name: str
    display_name: str
    description: str
    distros: list[str]

    @abstractmethod
    def run(self) -> bool:
        ...
