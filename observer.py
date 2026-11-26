import copy
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """Виды событий, о которых модуль уведомляет подписчиков"""
    DAMAGED = "повреждение"
    DESTROYED = "уничтожение"
    REPAIR = "ремонт"
    ACTIVATED = "активация"
    DEACTIVATED = "деактивация"
    STATE_CHANGED = "смена состояния"
    ENERGY_CHANGED = "изменение энергии"
    ENERGY_CONSUMED = "расход энергии"
    EFFICIENCY_CHANGED = "изменение эффективности"
    REJECTED = "отказ операции"


class ModuleEvent:
    """Событие модуля"""

    def __init__(self, event_type, module_id, damage=0, details=""):
        self.type = event_type
        self.module_id = module_id
        self.damage = damage  
        self.details = details
        self.timestamp = datetime.now()

    def __str__(self):
        time = self.timestamp.strftime("%H:%M:%S")
        text = f"{time} | модуль [{self.module_id}] | {self.type.value}"
        if self.damage > 0:
            text += f" | урон: {self.damage}"
        if self.details:
            text += f" | {self.details}"
        return text


class IObserver(ABC):
    """Интерфейс наблюдателя"""

    @abstractmethod
    def on_module_event(self, event):
        pass


class IObservable:
    """Наблюдаемый объект"""

    def __init__(self):
        self._observers = []

    def subscribe(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event):
        for observer in list(self._observers):
            observer.on_module_event(event)

    def _emit(self, event_type, damage=0, details=""):
        self.notify(ModuleEvent(event_type, self.id, damage, details))

    def __deepcopy__(self, memo):
        cls = self.__class__
        new_object = cls.__new__(cls)
        memo[id(self)] = new_object
        for key, value in self.__dict__.items():
            if key == "_observers":
                new_object.__dict__[key] = []
            else:
                new_object.__dict__[key] = copy.deepcopy(value, memo)
        return new_object
