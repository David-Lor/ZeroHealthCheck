"""CLI
Management of the CLI interface
"""

import argparse
import asyncio
from contextlib import suppress
from typing import List

from .hearth import Hearth
from .stethoscope import Stethoscope
from .const import BaseTask, HearthDefaults, StethoscopeDefaults

__all__ = ("run_cli",)


async def _run_services(objects: List[BaseTask]):
    """Given a list of BaseTask objects (Hearts and Stethoscopes), run all their async_run() methods with asyncio.gather
    """
    return await asyncio.gather(*[obj.async_run() for obj in objects])


def run_cli():
    """Run the CLI interface, and launch the services after parsing the user input
    """
    parser = argparse.ArgumentParser(
        description="Run the ZeroHealthcheck service as publisher, listener or both",
        add_help=False
    )
    parser.add_argument(
        "--help",
        action="help"
    )

    # Enable the sub-services
    parser.add_argument(
        "--publisher", "--hearth", "-p",
        action="store_true",
        help="Enable the publisher (Hearth)"
    )
    parser.add_argument(
        "--listener", "--stethoscope", "-l",
        action="store_true",
        help="Enable the listener (Stethoscope)"
    )

    # Hearth args
    parser.add_argument(
        "--publisher-port", "--hearth-port", "-pp", "-hp",
        type=int,
        default=HearthDefaults.zmq_port,
        help="ZeroMQ port for the publisher"
    )
    parser.add_argument(
        "--publisher-topic", "--hearth-topic", "-pt", "-ht",
        type=str,
        default=HearthDefaults.zmq_topic,
        help="ZeroMQ topic where to publish hearthbeats"
    )
    parser.add_argument(
        "--hearthbeat-frequency", "--hearth-frequency", "--beat-frequency", "-hf",
        type=float,
        default=HearthDefaults.hearthbeat_frequency,
        help="Frequency for hearth beats (seconds)"
    )

    # Stethoscopes hosts
    parser.add_argument(
        "--listener-host", "-h",
        type=str,
        action="append",
        help="Remote hosts to listen for hearthbeats. At least one required when the listener is enabled. "
             "Format: host | host:port | host@topic | host:port@topic "
             f"(default port={HearthDefaults.zmq_port} topic={HearthDefaults.zmq_topic})"
    )

    # Stethoscopes (common) args
    parser.add_argument(
        "--on-dead", "--dead", "--on-down", "--down", "-d",
        type=str,
        help="Command to run when a host is dead"
    )
    parser.add_argument(
        "--on-alive", "--alive", "-a",
        type=str,
        help="Command to run when a host is back online"
    )
    parser.add_argument(
        "--time-to-death", "-td", "-ttd",
        type=float,
        help="Time limit without receiving hearthbeats to declare a host as dead",
        default=StethoscopeDefaults.time_to_death
    )

    args = parser.parse_args()
    none_services = not args.publisher and not args.listener
    services = list()

    if args.publisher or none_services:
        hearth = Hearth(
            zmq_port=args.publisher_port,
            zmq_topic=args.publisher_topic,
            hearthbeat_frequency=args.hearthbeat_frequency
        )
        services.append(hearth)

    if args.listener_host and (args.listener or none_services and args.listener_host):
        for host_arg in args.listener_host:
            if "@" in host_arg:
                base, topic = host_arg.split("@")
                host_arg = base
            else:
                topic = HearthDefaults.zmq_topic

            if ":" in host_arg:
                host, port = host_arg.split(":")
            else:
                host = host_arg
                port = HearthDefaults.zmq_port

            stethoscope = Stethoscope(
                host=host,
                zmq_port=int(port),
                zmq_topic=topic,
                time_to_death=args.time_to_death,
                on_dead=args.on_dead,
                on_alive=args.on_alive
            )
            services.append(stethoscope)

    if not services:
        print("No services are going to run. If running as listener only, at least one host to listen is required")
        exit(1)

    with suppress(KeyboardInterrupt, InterruptedError):
        asyncio.run(_run_services(services))
