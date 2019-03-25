from datetime import datetime

from actors import Message, Actor, ActorSystem, PoisonPill


class Clock(Actor):

    class SayTime(Message):
        pass

    def receive(self, message: Message):
        if isinstance(message, Clock.SayTime):
            print(datetime.now())

    def on_destroy(self, pill: PoisonPill):
        print("Bye!")


def main():
    system = ActorSystem(rabbit_port=5672)
    clock = system.actor_of(Clock, None)
    while True:
        com = input('>>>')
        if com == 'a':
            clock.tell(Clock.SayTime, sender_id='')
        else:
            clock.tell(PoisonPill, sender_id='')
            break


if __name__ == '__main__':
    main()
