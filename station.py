import copy


class StationIterator:
    """Итератор для обхода модулей станции"""

    def __init__(self, modules):
        self._modules = list(modules)
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._modules):
            raise StopIteration
        module = self._modules[self._index]
        self._index += 1
        return module


class Station:
    """Станция"""

    def __init__(self, max_modules):
        if max_modules <= 0:
            raise ValueError("Максимальное количество модулей должно быть больше 0")
        self._max_modules = max_modules
        self._modules = []

    def get_max_modules(self):
        return self._max_modules

    def __len__(self):
        return len(self._modules)

    # добавление / удаление 

    def add_module(self, module):
        if len(self._modules) >= self._max_modules:
            raise ValueError("Станция заполнена, максимум модулей: " + str(self._max_modules))
        self._modules.append(module)

    def remove_by_id(self, module_id):
        for i in range(len(self._modules)):
            if self._modules[i].id == module_id:
                return self._modules.pop(i)
        raise ValueError("Модуль с id " + str(module_id) + " не найден")

    def remove_by_index(self, index):
        if index < 0 or index >= len(self._modules):
            raise IndexError("Неверный индекс: " + str(index))
        return self._modules.pop(index)

    def find_by_id(self, module_id):
        for module in self._modules:
            if module.id == module_id:
                return module
        return None

    def index_of(self, module):
        for i in range(len(self._modules)):
            if self._modules[i].id == module.id:
                return i
        raise ValueError("Модуля нет на станции")

    def move_module(self, from_index, to_index):
        n = len(self._modules)
        if from_index < 0 or from_index >= n or to_index < 0 or to_index >= n:
            raise IndexError("Неверный индекс при перемещении модуля")
        module = self._modules.pop(from_index)
        self._modules.insert(to_index, module)

    # копирование и перемещение 

    def __deepcopy__(self, memo):
        new_station = Station(self._max_modules)
        new_station._modules = [copy.deepcopy(m, memo) for m in self._modules]
        return new_station

    def transfer(self):
        new_station = Station(self._max_modules)
        new_station._modules = self._modules
        self._modules = []
        return new_station

    # итератор 

    def __iter__(self):
        return StationIterator(self._modules)

    def get_iterator(self):
        return StationIterator(self._modules)

    def sort_by_efficiency(self):
        self._modules.sort(key=lambda m: m.efficiency)
