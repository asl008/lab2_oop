

class ModuleTypeInfo:
    """Неизменяемые характеристики типа модуля, один объект на весь тип"""

    __slots__ = ("_type_name", "_max_durability", "_base_energy", "_capacity",
                 "_max_charge", "_cost", "_base_efficiency")

    def __init__(self, type_name, max_durability, base_energy, capacity,
                 max_charge, cost, base_efficiency=100):
        self._type_name = type_name
        self._max_durability = max_durability
        self._base_energy = base_energy
        self._capacity = capacity
        self._max_charge = max_charge
        self._cost = cost
        self._base_efficiency = base_efficiency

    def get_type_name(self):
        return self._type_name

    def get_max_durability(self):
        return self._max_durability

    def get_base_energy(self):
        return self._base_energy

    def get_capacity(self):
        return self._capacity

    def get_max_charge(self):
        return self._max_charge

    def get_cost(self):
        return self._cost

    def get_base_efficiency(self):
        return self._base_efficiency

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


class ModuleTypeInfoFactory:
    """Фабрика легковесов хранит созданные объекты и отдаёт уже существующие"""

    _cache = {}

    @classmethod
    def get(cls, type_name, max_durability, base_energy, capacity,
            max_charge, cost, base_efficiency=100):
        info = cls._cache.get(type_name)
        if info is None:
            info = ModuleTypeInfo(type_name, max_durability, base_energy, capacity,
                                  max_charge, cost, base_efficiency)
            cls._cache[type_name] = info
        return info

    @classmethod
    def count(cls):
        return len(cls._cache)
