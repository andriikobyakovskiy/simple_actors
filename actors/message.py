import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Message:
    message_id: str = field(repr=False, init=False, default_factory=uuid.uuid4().get_hex)
    sender_id: str


@dataclass(frozen=True)
class PoisonPill(Message):
    pass
