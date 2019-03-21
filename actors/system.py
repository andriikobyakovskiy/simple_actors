import threading

from dataclasses import dataclass
from typing import Dict, Union

from actors.actor import Props, Actor
from actors.message import Message


@dataclass(frozen=True)
class ActorRef:
    actor_id: str
    system: 'ActorSystem'

    def tell(self, message: Message):
        pass


class ActorSystem:

    def __init__(self):
        self._actors: Dict[str, Actor] = dict()
        self._threads: Dict[str, threading.Thread] = dict()

    def actor_of(self, actor_type: type, props: Union[Props, type(None)]) -> ActorRef:
        return ActorRef('', self)
