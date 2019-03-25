from dataclasses import dataclass

from actors.message import Message, PoisonPill


@dataclass(frozen=True)
class Props:
    pass


@dataclass(frozen=True)
class ActorRef:
    actor_id: str
    system: 'ActorSystem'

    def tell(self, message: type, **kwargs):
        self.system.add_message(self.actor_id, message(message_id=self.system._random_id(), **kwargs))


class Actor:

    def __init__(self, system: 'ActorSystem', actor_id: str):
        self._system = system
        self.ID = actor_id
        self._current_message: Message = None

    @property
    def sender(self):
        return ActorRef(self._current_message.sender_id, self._system)

    def receive(self, message: Message):
        raise NotImplementedError()

    def on_create(self, props: Props):
        pass

    def on_destroy(self, pill: PoisonPill):
        pass
