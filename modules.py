import copy
from abc import ABC, abstractmethod

from attributes import Durability, EnergyConsumption, Capacity, EnergyCharge
from damage import Damage
from observer import IObservable, EventType
from resource_package import ResourcePackage
from type_info import ModuleTypeInfoFactory

STATES = ("включён", "ремонт", "авария", "заблокирован")


class Module(IObservable, ABC):
    """Абстрактный базовый класс модуля"""

    _next_id = 1  

    @classmethod
    def reset_ids(cls):
        Module._next_id = 1

    def __init__(self, name, type_info, efficiency=None):
        super().__init__()
        self.id = Module._next_id
        Module._next_id += 1

        self.name = name
        self.type_info = type_info  
        self.durability = Durability(type_info.get_max_durability(),
                                     type_info.get_max_durability())
        self.energy = EnergyConsumption(type_info.get_base_energy())
        self.capacity = Capacity(type_info.get_capacity())
        self.charge = EnergyCharge(type_info.get_max_charge() // 2,
                                   type_info.get_max_charge())

        if efficiency is None:
            efficiency = type_info.get_base_efficiency()
        self.efficiency = 0
        self.set_efficiency(efficiency)

        self.state = "включён"
        self.active = False

    @abstractmethod
    def get_category(self):
        pass

    def get_type(self):
        return self.type_info.get_type_name()

    def get_oxygen_usage(self):
        return 0

    def clone(self):
        new_module = copy.deepcopy(self)
        new_module.id = Module._next_id
        Module._next_id += 1
        return new_module

    # изменение характеристик

    def set_efficiency(self, value):
        if value < 0 or value > 100:
            raise ValueError("Эффективность должна быть от 0 до 100")
        if value == self.efficiency:
            return
        old = self.efficiency
        self.efficiency = value
        self._emit(EventType.EFFICIENCY_CHANGED, details=f"{old}% -> {value}%")

    def set_energy_consumption(self, value):
        old = self.energy.get_value()
        self.energy.set_value(value)
        self._emit(EventType.ENERGY_CHANGED, details=f"потребление {old} -> {value} кВт")

    def set_state(self, new_state):
        if new_state not in STATES:
            raise ValueError("Неизвестное состояние: " + str(new_state))
        if new_state == self.state:
            return
        old = self.state
        was_active = self.active
        self.state = new_state
        if new_state != "включён":
            self.active = False
        self._emit(EventType.STATE_CHANGED, details=f"{old} -> {new_state}")
        if was_active and not self.active:
            self._emit(EventType.DEACTIVATED, details="из-за смены состояния")

    def activate(self):
        if self.state != "включён":
            self._emit(EventType.REJECTED,
                       details=f"активация невозможна, состояние: {self.state}")
            return False
        if self.active:
            return True
        self.active = True
        self._emit(EventType.ACTIVATED)
        return True

    def deactivate(self):
        if not self.active:
            return
        self.active = False
        self._emit(EventType.DEACTIVATED)

    def take_damage(self, amount):
        if amount < 0:
            raise ValueError("Урон не может быть отрицательным")
        before = self.durability.get_value()
        self.durability.decrease(amount)
        after = self.durability.get_value()
        lost = before - after
        if lost > 0:
            self._emit(EventType.DAMAGED, damage=lost, details=f"прочность {before} -> {after}")
            if after == 0:
                self._emit(EventType.DESTROYED, details="прочность исчерпана")
                self.set_state("авария")
        return lost

    def repair(self, amount):
        before = self.durability.get_value()
        self.durability.repair(amount)
        after = self.durability.get_value()
        if after > before:
            self._emit(EventType.REPAIR, details=f"прочность {before} -> {after}")
        return after - before

    def get_energy_usage(self, modifier=1.0):
        return int(self.energy.get_value() * modifier + 0.5)

    def consume_energy(self, modifier=1.0):
        if not self.active:
            return 0
        amount = self.get_energy_usage(modifier)
        self._emit(EventType.ENERGY_CONSUMED, details=f"израсходовано {amount} кВт")
        return amount

    # взаимодействие модулей 

    def transfer_energy(self, target, amount):
        if amount <= 0:
            raise ValueError("Количество энергии должно быть больше 0")
        if target is self:
            raise ValueError("Нельзя передавать энергию самому себе")
        if self.state != "включён" or target.state != "включён":
            self._emit(EventType.REJECTED,
                       details=f"передача '{self.name}' -> '{target.name}' невозможна: "
                               f"модули должны быть в состоянии 'включён'")
            return 0
        available = self.charge.take(amount)
        accepted = target.charge.add(available)
        self.charge.add(available - accepted)
        if accepted > 0:
            self._emit(EventType.ENERGY_CHANGED,
                         details=f"заряд {self.charge.get_value()}/{self.charge.get_max()}, "
                                 f"передано {accepted} -> '{target.name}'")
            target._emit(EventType.ENERGY_CHANGED,
                           details=f"заряд {target.charge.get_value()}/{target.charge.get_max()}, "
                                   f"получено {accepted} <- '{self.name}'")
        return accepted

    # перегрузка операций 

    def add_resources(self, package):
        accepted = self.charge.add(package.get_energy())
        if accepted > 0:
            self._emit(EventType.ENERGY_CHANGED,
                       details=f"заряд {self.charge.get_value()}/{self.charge.get_max()}, "
                               f"получено {accepted} от ресурсов")
        return accepted

    def apply_damage(self, damage):
        return self.take_damage(damage.get_amount())

    def scale_efficiency(self, modifier):
        if modifier < 0:
            raise ValueError("Множитель не может быть отрицательным")
        new_value = min(100, int(self.efficiency * modifier + 0.5))
        self.set_efficiency(new_value)

    def __add__(self, package):
        if not isinstance(package, ResourcePackage):
            return NotImplemented
        self.add_resources(package)
        return self

    def __sub__(self, damage):
        if not isinstance(damage, Damage):
            return NotImplemented
        self.apply_damage(damage)
        return self

    def __mul__(self, modifier):
        if isinstance(modifier, bool) or not isinstance(modifier, (int, float)):
            return NotImplemented
        self.scale_efficiency(modifier)
        return self

    def move_to_index(self, station, new_index):
        # перемещение модуля внутри станции
        old_index = station.index_of(self)
        station.move_module(old_index, new_index)

    def __str__(self):
        if self.active:
            work = "да"
        else:
            work = "нет"
        return (f"[{self.id}] {self.get_type()} '{self.name}' | "
                f"прочность: {self.durability.get_value()}, "
                f"энергия: {self.energy.get_value()} кВт, "
                f"заряд: {self.charge.get_value()}/{self.charge.get_max()}, "
                f"вместимость: {self.capacity.get_value()}, "
                f"эффективность: {self.efficiency}%, "
                f"состояние: {self.state}, активен: {work}")


# Промежуточные категории 

class ResidentialModule(Module):
    """Жилой модуль"""

    def get_category(self):
        return "residential"

    def get_oxygen_usage(self):
        return self.capacity.get_value() * 2


class EnergyModule(Module):
    """Энергетический модуль"""

    def get_category(self):
        return "energy"


class ResearchModule(Module):
    """Исследовательский модуль"""

    def get_category(self):
        return "research"


# Жилые 

class CrewCabin(ResidentialModule):
    def __init__(self, name, efficiency=None):
        info = ModuleTypeInfoFactory.get("CrewCabin", max_durability=100, base_energy=10,
                                         capacity=4, max_charge=50, cost=300)
        super().__init__(name, info, efficiency)


class MedicalCabin(ResidentialModule):
    def __init__(self, name, efficiency=None):
        info = ModuleTypeInfoFactory.get("MedicalCabin", max_durability=100, base_energy=25,
                                         capacity=2, max_charge=50, cost=700)
        super().__init__(name, info, efficiency)


# Энергетические 

class SolarModule(EnergyModule):
    def __init__(self, name, efficiency=None):
        info = ModuleTypeInfoFactory.get("SolarModule", max_durability=80, base_energy=5,
                                         capacity=0, max_charge=100, cost=400)
        super().__init__(name, info, efficiency)


class ReactorModule(EnergyModule):
    def __init__(self, name, efficiency=None):
        info = ModuleTypeInfoFactory.get("ReactorModule", max_durability=150, base_energy=40,
                                         capacity=0, max_charge=200, cost=1500)
        super().__init__(name, info, efficiency)


# Исследовательские 

class BiologyLab(ResearchModule):
    def __init__(self, name, efficiency=None):
        # вместимость - количество образцов
        info = ModuleTypeInfoFactory.get("BiologyLab", max_durability=100, base_energy=30,
                                         capacity=50, max_charge=50, cost=800)
        super().__init__(name, info, efficiency)


class PhysicsLab(ResearchModule):
    def __init__(self, name, efficiency=None):
        info = ModuleTypeInfoFactory.get("PhysicsLab", max_durability=120, base_energy=60,
                                         capacity=20, max_charge=80, cost=1200)
        super().__init__(name, info, efficiency)
