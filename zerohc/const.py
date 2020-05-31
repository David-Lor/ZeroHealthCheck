"""CONST
Const variables, attributes, default values and base classes
"""

import zmq.asyncio
import abc
import asyncio
from contextlib import suppress

__all__ = ("BaseTask", "HearthDefaults", "StethoscopeDefaults")


class HearthDefaults:
    """Default values for Hearth publisher
    """
    zmq_port = 5555
    zmq_topic = "hearthbeat"
    hearthbeat_frequency = 5.0


class StethoscopeDefaults:
    """Default values for Stethoscope listener
    """
    time_to_death = 15


class BaseTask(abc.ABC):
    zmq_topic: str
    zmq_port: int
    zmq_context: zmq.asyncio.Context
    zmq_socket = None

    def run(self):
        """Start running the object functionality through asyncio.run, from a sync context
        """
        with suppress(KeyboardInterrupt, InterruptedError):
            asyncio.run(self.async_run())

    @abc.abstractmethod
    async def async_run(self):
        """Start running the object functionality asynchronously. This method implements the core functionality
        """
        ...
