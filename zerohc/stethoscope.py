"""STETHOSCOPE
"""

import zmq
import zmq.asyncio
import subprocess

from .const import BaseTask, HearthDefaults, StethoscopeDefaults
from .logger import Logger, LoggerServices

__all__ = ("Stethoscope",)


class Stethoscope(BaseTask):
    """The stethoscope listens for a remote Hearth through ZeroMQ.
    When the hearth stops beating, or starts beating after stopped, runs the respective commands for notification.
    """
    def __init__(
            self,
            logger: Logger,
            host: str,
            on_dead: str = None,
            on_alive: str = None,
            time_to_death: float = StethoscopeDefaults.time_to_death,
            zmq_port: int = HearthDefaults.zmq_port,
            zmq_topic: str = HearthDefaults.zmq_topic
    ):
        """
        :param logger: Logger instance
        :param host: host of remote Hearth to listen to
        :param on_dead: command to execute when Hearth stops beating
        :param on_alive: command to execute when Hearth starts beating again
        :param time_to_death: time without listening hearthbeats to consider remote Hearth dead
        :param zmq_port: ZMQ port of remote Hearth
        :param zmq_topic: ZMQ topic where hearthbeats are published
        """
        self.logger = logger.bind(
            service=LoggerServices.Stethoscope,
            host=host
        )
        self.host = host
        self.zmq_port = zmq_port
        self.time_to_death = time_to_death
        self.zmq_topic = zmq_topic
        self.hearth_alive = True

        self.on_dead = None
        self.on_alive = None
        if on_dead:
            self.on_dead = lambda: self.__run_command(on_dead)
        else:
            self.logger.warning("No \"on dead\" command specified")
        if on_alive:
            self.on_alive = lambda: self.__run_command(on_alive)
        else:
            self.logger.warning("No \"on alive\" command specified")

        self.zmq_context = zmq.asyncio.Context()
        self.zmq_socket = None

    async def async_run(self):
        self.hearth_alive = True
        # noinspection PyUnresolvedReferences
        self.zmq_socket = self.zmq_context.socket(zmq.SUB)
        # noinspection PyUnresolvedReferences
        self.zmq_socket.setsockopt(zmq.RCVTIMEO, int(self.time_to_death * 1000))
        # noinspection PyUnresolvedReferences
        self.zmq_socket.setsockopt(zmq.SUBSCRIBE, self.zmq_topic.encode())

        # If remote ZMQ publisher is offline, this will not fail
        self.zmq_socket.connect(f"tcp://{self.host}:{self.zmq_port}")

        self.logger.info("Stethoscope starts listening")

        try:
            while True:
                try:
                    # NOTE the first hearthbeat published is usually not received
                    message = (await self.zmq_socket.recv()).decode()

                    self.logger.debug("Received hearthbeat")
                    self.logger.trace(f"Rx: {message}")

                    if not self.hearth_alive:
                        # Target alive after being dead
                        self.logger.info("Hearth is alive, started beating again")
                        if self.on_alive:
                            self.on_alive()

                    self.hearth_alive = True

                except zmq.error.Again:
                    if self.hearth_alive:
                        # Target died after being alive
                        self.logger.warning("Hearth died, stopped beating or could not listen it")
                        if self.on_dead:
                            self.on_dead()

                    self.hearth_alive = False

        finally:
            self.zmq_socket.close()
            self.zmq_socket = None
            self.logger.info("Stethoscope stopped listening (socket closed)")

    def __run_command(self, cmd):
        # TODO Run command async
        # TODO Split string and shell=False?
        _cmd = cmd.replace("%ip", self.host)
        self.logger.debug(f"Running command \"{_cmd}\"...")

        try:
            r = subprocess.check_output(_cmd, shell=True)
            self.logger.debug(f"Command run successfully {f'with output: {r}' if r else ''}")

        except subprocess.CalledProcessError as error:
            code = error.returncode
            self.logger.error(f"Command failed with return code {code}")
