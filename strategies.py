from abc import ABC, abstractmethod

from damage import RADIATION
from modules import Module, EnergyModule, ReactorModule, ResidentialModule, ResearchModule


class IInteractionStrategy(ABC):
    """Интерфейс стратегии применить воздействие к модулю"""

    @abstractmethod
    def apply(self, module, damage):
        pass


class DefaultStrategy(IInteractionStrategy):
    """Стратегия по умолчанию (для новых типов модулей) урон без изменений"""

    def apply(self, module, damage):
        module -= damage


class EnergyModuleStrategy(IInteractionStrategy):
    """Энергетические модули электроника и панели сильно страдают от излучения"""

    def apply(self, module, damage):
        if damage.get_type() == RADIATION:
            module -= damage.scaled(1.5)
            module *= max(0.0, 1 - damage.get_amount() / 100)
        else:
            module -= damage


class ReactorModuleStrategy(IInteractionStrategy):
    """Реактор защитный гасит часть урона, но при сильном износе срабатывает аварийная защита"""

    def apply(self, module, damage):
        module -= damage.scaled(0.5)
        limit = module.durability.get_max() * 0.25
        if module.durability.get_value() <= limit:
            module.set_state("авария")


class CrewModuleStrategy(IInteractionStrategy):
    """Жилые модули обшивка держит удар, но экипаж страдает и работает хуже"""

    def apply(self, module, damage):
        module -= damage
        module *= max(0.0, 1 - damage.get_amount() / 200)


class ResearchModuleStrategy(IInteractionStrategy):
    """Исследовательские модули приборы сбиваются от любого воздействия"""

    def apply(self, module, damage):
        module -= damage.scaled(0.8)
        module *= max(0.0, 1 - damage.get_amount() / 100)


class StrategyContext:
    """Контекст подбирает стратегию по типу модуля"""

    def __init__(self):
        self._strategies = {}
        self._default = DefaultStrategy()

    def register(self, module_class, strategy):
        self._strategies[module_class] = strategy

    def select(self, module):
        for cls in type(module).__mro__:
            if cls in self._strategies:
                return self._strategies[cls]
        return self._default

    def apply(self, module, damage):
        self.select(module).apply(module, damage)


def default_context():
    """Контекст со стратегиями для всех категорий модулей"""
    context = StrategyContext()
    context.register(Module, DefaultStrategy())
    context.register(EnergyModule, EnergyModuleStrategy())
    context.register(ReactorModule, ReactorModuleStrategy())
    context.register(ResidentialModule, CrewModuleStrategy())
    context.register(ResearchModule, ResearchModuleStrategy())
    return context
