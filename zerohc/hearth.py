"""HEARTH
"""

import zmq
import zmq.asyncio
import asyncio
import json
from time import time

from .const import BaseTask, HearthDefaults
from .logger import Logger, LoggerServices

__all__ = ("Hearth",)


class Hearth(BaseTask):
    """The hearth publishes periodically its hearthbeats on a ZeroMQ topic, to let listeners know
    the host/service is alive.
    """
    def __init__(
            self,
            logger: Logger,
            zmq_port: int = HearthDefaults.zmq_port,
            zmq_topic: str = HearthDefaults.zmq_topic,
            hearthbeat_frequency: float = HearthDefaults.hearthbeat_frequency
    ):
        """
        :param logger: logger instance
        :param zmq_port: ZMQ topic for publishing
        :param zmq_topic: topic where publish hearthbeats
        :param hearthbeat_frequency: time span between hearthbeats
        """
        self.logger = logger.bind(
            service=LoggerServices.Hearth
        )
        self.hearthbeat_frequency = hearthbeat_frequency
        self.zmq_topic = zmq_topic
        self.zmq_port = int(zmq_port)

        self.zmq_context = zmq.asyncio.Context()
        self.zmq_socket = None
        self.hearthbeat_counter = 0
        self.hearth_beating_since = 0

        self.logger.debug("Initialized Hearth")

    async def async_run(self):
        self.hearthbeat_counter = 0

        # noinspection PyUnresolvedReferences
        self.zmq_socket = self.zmq_context.socket(zmq.PUB)
        self.zmq_socket.bind(f"tcp://*:{self.zmq_port}")

        self.logger.info("Hearth starts beating")

        try:
            self.hearth_beating_since = int(time())
            while True:
                await self._send_hearthbeat()
                await asyncio.sleep(self.hearthbeat_frequency)

        finally:
            self.zmq_socket.close()
            self.zmq_socket = None
            self.logger.info("Hearth stopped beating (socket closed)")

    async def _send_message(self, message: str):
        await self.zmq_socket.send(f"{self.zmq_topic} {message}".encode())
        self.logger.trace(f"Tx: {message}")

    async def _send_hearthbeat(self):
        hearthbeat = self._get_hearthbeat()
        message = json.dumps(hearthbeat)
        await self._send_message(message)
        self.logger.debug("Hearth beated")

    def _get_hearthbeat(self):
        # self.hearthbeat_counter += 1
        return {
            # "n": self.hearthbeat_counter,
            "time": int(time()),
            "beating_since": self.hearth_beating_since
        }
