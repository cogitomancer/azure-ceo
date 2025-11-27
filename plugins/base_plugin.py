from __future__ import annotations
from typing import Callable, Dict, Any

from semantic_kernel.agents import ChatCompletionAgent


class BasePlugin:
    """
    Base class for all plugins in the Azure CEO marketing agent system.

    Each plugin must:
        - Define get_functions(): returning a dict[str, callable]
        - Use async methods for actual behavior
        - Provide register(agent): automatically attaches functions to the agent
    """

    def get_functions(self) -> Dict[str, Callable]:
        """
        Subclasses override this and return:
            {
                "function_name": async_function_reference,
                ...
            }
        """
        raise NotImplementedError("Plugins must implement get_functions().")

    def register(self, agent: ChatCompletionAgent):
        """
        Registers all plugin functions on the agent by name.
        This allows the agent to call them as SK tools.
        """

        funcs = self.get_functions()
        if not isinstance(funcs, dict):
            raise TypeError(
                f"{self.__class__.__name__}.get_functions() must return a dict."
            )

        for name, fn in funcs.items():
            if not callable(fn):
                raise TypeError(
                    f"Function '{name}' in plugin {self.__class__.__name__} is not callable."
                )

            agent.add_function(
                function=fn,
                name=name,
                description=f"{self.__class__.__name__}.{name}"
            )
