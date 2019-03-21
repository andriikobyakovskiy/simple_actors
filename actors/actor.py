from dataclasses import dataclass

from actors.message import Message, PoisonPill


@dataclass(frozen=True)
class Props:
    pass


class Actor:

    def __init__(self, system: 'ActorSystem', actor_id: str):
        self._system = system
        self.ID = actor_id

    def receive(self, message: Message):
        raise NotImplementedError()

    def on_create(self, props: Props):
        pass

    def on_destroy(self, pill: PoisonPill):
        pass
