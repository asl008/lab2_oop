import random
from abc import ABC, abstractmethod

from damage import Damage, RADIATION, IMPACT
from logging_proxy import LogSource
from resource_package import ResourcePackage
from strategies import default_context

RESOURCE = "ресурсы"
ANOMALY = "аномалия"


class ExternalObject(ABC):
    """Абстрактный внешний объект"""

    def __init__(self, name, type_, strength):
        self._name = name
        self._type = type_
        self._strength = strength

    def get_name(self):
        return self._name

    def get_type(self):
        return self._type

    def get_strength(self):
        return self._strength

    @abstractmethod
    def interact(self, center, module):
        """Взаимодействие объекта с одним модулем и командным центром"""
        pass

    def affect_station(self, center):
        for module in center.get_modules():
            self.interact(center, module)


class SolarStorm(ExternalObject):
    """Солнечная буря радиация, повреждения и сбой электроники"""

    ELECTRONICS_LOSS = 2

    def __init__(self, power=20, strategies=None):
        super().__init__("Солнечная буря", RADIATION, power)
        if strategies is None:
            strategies = default_context()
        self._strategies = strategies

    def interact(self, center, module):
        amount = int(self._strength * center.get_damage_factor() + 0.5)
        damage = Damage(amount, self._type)
        center.log(LogSource.OBJECT, f"Буря облучает '{module.name}': {damage}")
        self._strategies.apply(module, damage)
        center -= ResourcePackage(energy=self.ELECTRONICS_LOSS)


class MeteorShower(ExternalObject):
    """Метеоритный поток физические удары по случайным модулям"""

    def __init__(self, hits=3, min_damage=8, max_damage=20, rng=None):
        super().__init__("Метеоритный поток", IMPACT, max_damage)
        self._hits = hits
        self._min_damage = min_damage
        self._max_damage = max_damage
        if rng is None:
            rng = random.Random()
        self._rng = rng

    def interact(self, center, module):
        amount = self._rng.randint(self._min_damage, self._max_damage)
        damage = Damage(int(amount * center.get_damage_factor() + 0.5), self._type)
        center.log(LogSource.OBJECT, f"Метеорит попал в '{module.name}': урон {damage}")
        module -= damage

    def affect_station(self, center):
        modules = center.get_modules()
        if len(modules) == 0:
            return
        for _ in range(self._hits):
            self.interact(center, self._rng.choice(modules))


class CargoContainer(ExternalObject):
    """Грузовой контейнер ресурсы для станции и запчасти для ремонта"""

    def __init__(self, energy=150, oxygen=80, repair=15, safety_level=5):
        super().__init__("Грузовой контейнер", RESOURCE, energy)
        self._package = ResourcePackage(energy, oxygen, safety_level)
        self._repair = repair

    def interact(self, center, module):
        center += self._package
        restored = module.repair(self._repair)
        center.log(LogSource.OBJECT,
                   f"Контейнер пристыкован к '{module.name}': +{self._package}, "
                   f"прочность модуля +{restored}")

    def affect_station(self, center):
        modules = center.get_modules()
        if len(modules) == 0:
            return
        worst = min(modules, key=lambda m: m.durability.get_value() / m.durability.get_max())
        self.interact(center, worst)


class SpaceAnomaly(ExternalObject):
    """Космическая аномалия непредсказуемый эффект"""

    def __init__(self, strength=2, rng=None):
        super().__init__("Космическая аномалия", ANOMALY, strength)
        if rng is None:
            rng = random.Random()
        self._rng = rng
        self._effects = [self._teleport, self._double_energy, self._disable_module,
                         self._power_surge]

    def interact(self, center, module):
        effect = self._rng.choice(self._effects)
        effect(center, module)

    def affect_station(self, center):
        modules = center.get_modules()
        if len(modules) == 0:
            return
        self.interact(center, self._rng.choice(modules))

    def _teleport(self, center, module):
        new_index = self._rng.randrange(len(center))
        center.move_module(module, new_index)
        center.log(LogSource.OBJECT, f"Аномалия телепортировала '{module.name}' на позицию {new_index}")

    def _double_energy(self, center, module):
        center *= self._strength
        center.log(LogSource.OBJECT, f"Аномалия умножила запас энергии станции на {self._strength}: "
                                     f"{center.get_energy()}")

    def _disable_module(self, center, module):
        module.set_state("заблокирован")
        center.log(LogSource.OBJECT, f"Аномалия отключила модуль '{module.name}'")

    def _power_surge(self, center, module):
        new_value = module.energy.get_value() * self._strength
        module.set_energy_consumption(new_value)
        center.log(LogSource.OBJECT, f"Аномалия вызвала скачок: '{module.name}' теперь потребляет "
                                     f"{new_value} кВт")
