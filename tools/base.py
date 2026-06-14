from abc import ABC, abstractmethod


class Tool(ABC):
    name: str
    display_name: str
    description: str
    distros: list[str]
    mutates_system: bool = True
    requires_network: bool = False
    requires_sudo: bool = False
    safe_for_run_all: bool = False

    @abstractmethod
    def run(self) -> bool | None:
        """Run the tool.

        Returns:
            True/False to show "press enter" prompt, None to skip it.
        """
        ...

    def run_all(self) -> bool | None:
        """Run the tool in non-destructive run-all mode."""
        return self.run()
