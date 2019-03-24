import threading
import uuid

import pika

from dataclasses import dataclass
from typing import Dict, Union

from actors.actor import Props, Actor
from actors.message import Message, MessageJSONEncoder, MessageJSONDecoder


@dataclass(frozen=True)
class ActorRef:
    actor_id: str
    system: 'ActorSystem'

    def tell(self, message: Message):
        self.system.add_message(self.actor_id, message)


class ActorSystem:

    MAIN_EXCHANGE_NAME = 'actors_routing_queue'

    def _actor_thread(self, actor_id: str):
        new_channel = self._connection.channel()
        self._channels[actor_id] = new_channel
        decoder = MessageJSONDecoder()
        new_channel.queue_declare(name=actor_id)
        new_channel.queue_bind(exchange=self.MAIN_EXCHANGE_NAME, queue=actor_id, routing_key=actor_id)

        def callback(ch, method, properties, body):
            self._actors[actor_id].receive(decoder.decode(body))

        new_channel.basic_consume(callback, queue=actor_id, no_ack=True)
        new_channel.start_consuming()

    def add_message(self, actor_id: str, message: Message):
        self._main_channel.basic_publish(
            exchange=self.MAIN_EXCHANGE_NAME,
            routing_key=actor_id,
            body=MessageJSONEncoder().encode(message)
        )

    def __init__(self, rabbit_host: str = '127.0.0.1', rabbit_port: int = 5672):
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host, port=rabbit_port))
        self._actors: Dict[str, Actor] = dict()
        self._threads: Dict[str, threading.Thread] = dict()
        self._channels: Dict[str, pika.BaseConnection] = dict()
        self._main_channel = self._connection.channel()
        self._main_channel.exchange_declare(
            exchange=self.MAIN_EXCHANGE_NAME,
            exchange_type='direct',
        )

    def actor_of(self, actor_type: type, props: Union[Props, type(None)]) -> ActorRef:
        new_actor_id = uuid.uuid4().hex
        self._actors[new_actor_id] = actor_type(self, new_actor_id)
        self._actors[new_actor_id].on_create(props)
        self._threads[new_actor_id] = threading.Thread(
            target=self._actor_thread,
            args=(new_actor_id,)
        )
        self._threads[new_actor_id].start()
        return ActorRef(new_actor_id, self)
