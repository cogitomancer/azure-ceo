from .blueprint import bp

#Importing the definition so that the decorators are registered
#if we split the agents intp 7 different files we would need to import them here
from . import agent_definition

__all__ = ["bp"]