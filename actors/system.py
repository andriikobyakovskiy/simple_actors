import threading
import uuid

import pika

from typing import Dict, Union

from actors.actor import Props, Actor, ActorRef
from actors.message import Message, MessageJSONEncoder, MessageJSONDecoder, PoisonPill


class ActorSystem:

    MAIN_EXCHANGE_NAME = 'actors_routing_queue'

    @classmethod
    def _random_id(cls):
        return uuid.uuid4().hex

    def _actor_thread(self, actor_id: str):
        new_connection = pika.BlockingConnection(self._conn_params)
        self._connections[actor_id] = new_connection
        new_channel = new_connection.channel()
        self._channels[actor_id] = new_channel
        decoder = MessageJSONDecoder()
        new_channel.queue_declare(queue=actor_id)
        new_channel.queue_bind(exchange=self.MAIN_EXCHANGE_NAME, queue=actor_id, routing_key=actor_id)

        def callback(ch, method, properties, body):
            message_string = body.decode()
            print("Got body: " + message_string)
            message = decoder.decode(message_string)
            print("Got message: " + str(message))
            if isinstance(message, PoisonPill):
                new_channel.stop_consuming()
                self._actors[actor_id].on_destroy(message)
            self._actors[actor_id]._current_message = message
            self._actors[actor_id].receive(message)

        new_channel.basic_consume(callback, queue=actor_id, no_ack=True)
        new_channel.start_consuming()

    def add_message(self, actor_id: str, message: Message):
        self._main_channel.basic_publish(
            exchange=self.MAIN_EXCHANGE_NAME,
            routing_key=actor_id,
            body=MessageJSONEncoder().encode(message)
        )

    def __init__(self, rabbit_host: str = '127.0.0.1', rabbit_port: int = 5672):
        self._conn_params = pika.ConnectionParameters(host=rabbit_host, port=rabbit_port)
        self._connection = pika.BlockingConnection(self._conn_params)
        self._actors: Dict[str, Actor] = dict()
        self._threads: Dict[str, threading.Thread] = dict()
        self._channels: Dict[str, pika.BaseConnection] = dict()
        self._connections: Dict[str, pika.BaseConnection] = dict()
        self._main_channel = self._connection.channel()
        self._main_channel.exchange_declare(
            exchange=self.MAIN_EXCHANGE_NAME,
            exchange_type='direct',
        )

    def actor_of(self, actor_type: type, props: Union[Props, type(None)]) -> ActorRef:
        new_actor_id = 'actor_' + uuid.uuid4().hex
        self._actors[new_actor_id] = actor_type(self, new_actor_id)
        self._actors[new_actor_id].on_create(props)
        self._threads[new_actor_id] = threading.Thread(
            target=self._actor_thread,
            args=(new_actor_id,)
        )
        self._threads[new_actor_id].start()
        return ActorRef(new_actor_id, self)
