import dataclasses
import uuid
import json

from json.decoder import WHITESPACE
from dataclasses import dataclass, field


class MetaMessage(type):

    _registered_constructors = dict()

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)
        cls._registered_constructors[name] = x.__init__
        return x

    def from_json(cls, dumped_message):
        message_dict = json.loads(dumped_message)
        message_class = message_dict.pop('_message_class')


def _random_id():
    return uuid.uuid4().hex


@dataclass(frozen=True)
class Message(metaclass=MetaMessage):
    message_id: str = field(repr=False, init=False, default_factory=_random_id)
    sender_id: str


@dataclass(frozen=True)
class PoisonPill(Message):
    pass


class MessageJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Message):
            data = dataclasses.asdict(o)
            data['_message_class'] = type(o).__name__
            return data
        return super().default(o)


class MessageJSONDecoder(json.JSONDecoder):

    def decode(self, s, _w=WHITESPACE.match):
        raw = super().decode(s, _w)
        if isinstance(raw, dict) and '_message_class' in raw:
            message_class = raw.pop('_message_class')
            message = MetaMessage._registered_constructors[message_class](**raw)
            return message
        else:
            return raw
