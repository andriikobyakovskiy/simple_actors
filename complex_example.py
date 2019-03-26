import datetime
import uuid

from dataclasses import dataclass

from actors import ActorSystem, Actor, Message, PoisonPill, Props


def _request_id_factory():
    return uuid.uuid4().hex


class Timer(Actor):

    class TimeUnits:
        HOURS = 'hours'
        MINUTES = 'minutes'
        SECONDS = 'seconds'

    @dataclass(frozen=True)
    class TimerProps(Props):
        units: str

    @dataclass(frozen=True)
    class GetTime(Message):
        request_id: str

    @dataclass(frozen=True)
    class ResultTime(Message):
        request_id: str
        units_passed: int

    def __init__(self, system: 'ActorSystem', actor_id: str):
        super().__init__(system, actor_id)
        self._creation_time = datetime.datetime.now()

    def on_create(self, props: Props):
        super().on_create(props)
        if isinstance(props, Timer.TimerProps):
            self._units = props.units
        else:
            raise Exception("Wrong Properties class")

    def _get_units_passed(self):
        seconds = (datetime.datetime.now() - self._creation_time).seconds
        if self._units == Timer.TimeUnits.SECONDS:
            return seconds
        elif self._units == Timer.TimeUnits.MINUTES:
            return seconds // 60
        elif self._units == Timer.TimeUnits.HOURS:
            return seconds // 3600

    def receive(self, message: Message):
        if isinstance(message, Timer.GetTime):
            self.sender.tell(
                message=Timer.ResultTime,
                sender_id=self.ID,
                request_id=message.request_id,
                units_passed=self._get_units_passed()
            )


class TimerManager(Actor):

    @dataclass(frozen=True)
    class CreateTimer(Message):
        units: str

    class PrintTimers(Message):
        pass

    def __init__(self, system: 'ActorSystem', actor_id: str):
        super().__init__(system, actor_id)
        self._timers = dict()
        self._requests = dict()

    def receive(self, message: Message):
        if isinstance(message, TimerManager.CreateTimer):
            new_timer = self._system.actor_of(Timer, Timer.TimerProps(units=message.units))
            self._timers[new_timer.actor_id] = new_timer

        elif isinstance(message, TimerManager.PrintTimers):
            request_id = _request_id_factory()
            self._requests[request_id] = dict(awaiting=self._timers.keys(), responses=dict())
            for timer in self._timers.values():
                timer.tell(
                    message=Timer.GetTime,
                    sender_id=self.ID,
                    request_id=request_id
                )

        elif isinstance(message, Timer.ResultTime) and message.request_id in self._requests:
            self._requests[message.request_id]['responses'][message.sender_id] = message.units_passed
            if set(self._requests[message.request_id]['responses']) == \
                set(self._requests[message.request_id]['awaiting']):
                print("Timer results: {}".format(self._requests[message.request_id]['responses']))
                del self._requests[message.request_id]

    def on_destroy(self, pill: PoisonPill):
        for timer in self._timers.values():
            timer.tell(message=PoisonPill, sender_id=self.ID)
        super().on_destroy(pill)


def main():
    system = ActorSystem(rabbit_port=6798)
    manager = system.actor_of(TimerManager, None)
    while True:
        com = input('>>>')
        if com == 'collect':
            manager.tell(TimerManager.PrintTimers, sender_id='')
        elif com == Timer.TimeUnits.SECONDS:
            manager.tell(TimerManager.CreateTimer, sender_id='', units=Timer.TimeUnits.SECONDS)
        elif com == Timer.TimeUnits.MINUTES:
            manager.tell(TimerManager.CreateTimer, sender_id='', units=Timer.TimeUnits.MINUTES)
        elif com == Timer.TimeUnits.HOURS:
            manager.tell(TimerManager.CreateTimer, sender_id='', units=Timer.TimeUnits.HOURS)
        else:
            break
    manager.tell(PoisonPill, sender_id='')


if __name__ == '__main__':
    main()
