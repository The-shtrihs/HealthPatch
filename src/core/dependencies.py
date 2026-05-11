from fastapi import Request

from src.shared.infrastructure.event_bus_interface import IEventBus


def get_event_bus(request: Request) -> IEventBus:
    return request.app.state.event_bus