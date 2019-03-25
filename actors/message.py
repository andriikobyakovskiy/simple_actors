import dataclasses
import functools
import uuid
import json

from json.decoder import WHITESPACE
from dataclasses import dataclass, field


class MetaMessage(type):

    _registered_constructors = dict()

    def __new__(mcs, name, bases, dct):
        x = super().__new__(mcs, name, bases, dct)
        mcs._registered_constructors[name] = lambda *args, **kwargs: x(*args, **kwargs)
        return x


def _random_id():
    return uuid.uuid4().hex


@dataclass(frozen=True)
class Message(metaclass=MetaMessage):
    sender_id: str = field(repr=False)
    message_id: str = field(repr=False, default_factory=_random_id)


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
