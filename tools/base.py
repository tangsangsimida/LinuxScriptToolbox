from abc import ABC, abstractmethod


class Tool(ABC):
    name: str
    display_name: str
    description: str
    distros: list[str]

    @abstractmethod
    def run(self) -> bool | None:
        """Run the tool.

        Returns:
            True/False to show "press enter" prompt, None to skip it.
        """
        ...
