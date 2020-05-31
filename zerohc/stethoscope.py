"""STETHOSCOPE
"""

import zmq
import zmq.asyncio
import subprocess

from .const import BaseTask, HearthDefaults, StethoscopeDefaults

__all__ = ("Stethoscope",)


class Stethoscope(BaseTask):
    """The stethoscope listens for a remote Hearth through ZeroMQ.
    When the hearth stops beating, or starts beating after stopped, runs the respective commands for notification.
    """
    def __init__(
            self,
            host: str,
            on_dead: str = None,
            on_alive: str = None,
            time_to_death: float = StethoscopeDefaults.time_to_death,
            zmq_port: int = HearthDefaults.zmq_port,
            zmq_topic: str = HearthDefaults.zmq_topic
    ):
        self.host = host
        self.zmq_port = zmq_port
        self.time_to_death = time_to_death
        self.zmq_topic = zmq_topic
        self.hearth_alive = True

        # TODO when using logger, WARN if no commands specified
        self.on_dead = None
        self.on_alive = None
        if on_dead:
            self.on_dead = lambda: self.__run_command(on_dead)
        if on_alive:
            self.on_alive = lambda: self.__run_command(on_alive)

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

        try:
            while True:
                try:
                    # NOTE the first hearthbeat published is usually not received
                    message = (await self.zmq_socket.recv()).decode()
                    print(f"({self.host}:{self.zmq_port}) RX {message}")

                    if not self.hearth_alive:
                        # Target alive after being dead
                        print(f"({self.host}:{self.zmq_port}) ALIVE")
                        if self.on_alive:
                            self.on_alive()

                    self.hearth_alive = True

                except zmq.error.Again:
                    if self.hearth_alive:
                        # Target died after being alive
                        print(f"({self.host}:{self.zmq_port}) DEAD")
                        if self.on_dead:
                            self.on_dead()

                    self.hearth_alive = False

        finally:
            self.zmq_socket.close()
            self.zmq_socket = None
            print("Socket closed")

    def __run_command(self, cmd):
        # TODO Split string and shell=False?
        _cmd = cmd.replace("%ip", self.host)
        # TODO Suppress command errors (but log output and statuscode)
        print(f"Running command {_cmd}")
        subprocess.check_output(_cmd, shell=True)
