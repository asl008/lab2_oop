from environment_proxy import EnvironmentProxy
from logging_proxy import LoggingProxy, LogSource
from observer import IObserver, EventType
from resource_package import ResourcePackage
from station import Station


CRITICAL_RATIO = 0.3
DAMAGE_SAFETY_PENALTY = 1


class CommandCenter(IObserver):
    """Командный центр"""

    def __init__(self, max_modules, energy=1000, oxygen=500, safety_level=50):
        if energy < 0 or oxygen < 0:
            raise ValueError("Запасы не могут быть отрицательными")
        self._modules = Station(max_modules)  
        self._energy = energy
        self._oxygen = oxygen
        self._safety_level = 0
        self.set_safety_level(safety_level)
        self._current_environment = None
        self._journal = []  
        self._critical = set()  
        self._total_damage = 0
        self._verbose = False
        self._logger = LoggingProxy()

    # учёт модулей 

    def create_module(self, factory, category, name, efficiency=100):
        method = getattr(factory, "create_" + str(category) + "_module", None)
        if method is None:
            raise ValueError("Фабрика не умеет создавать модули категории: " + str(category))
        module = method(name, efficiency)
        self.add_module(module)
        return module

    def add_module(self, module):
        self._modules.add_module(module)
        module.subscribe(self) 

    def remove_module_by_id(self, module_id):
        module = self._modules.remove_by_id(module_id)
        module.unsubscribe(self)
        self._critical.discard(module.id)
        return module

    def remove_module_by_index(self, index):
        module = self._modules.remove_by_index(index)
        module.unsubscribe(self)
        self._critical.discard(module.id)
        return module

    def find_module(self, module_id):
        return self._modules.find_by_id(module_id)

    def move_module(self, module, new_index):
        module.move_to_index(self._modules, new_index)

    def get_modules(self):
        return list(self._modules)

    def __len__(self):
        return len(self._modules)

    def __iter__(self):
        return iter(self._modules)

    # характеристики станции 

    def get_energy(self):
        return self._energy

    def get_oxygen(self):
        return self._oxygen

    def get_max_modules(self):
        return self._modules.get_max_modules()

    def get_safety_level(self):
        return self._safety_level

    def set_safety_level(self, value):
        if value < 0 or value > 100:
            raise ValueError("Уровень безопасности должен быть от 0 до 100")
        self._safety_level = value

    def get_resistance(self):
        return 1 - self._safety_level / 200

    def get_total_damage(self):
        return self._total_damage

    def get_total_cost(self):
        return sum(m.type_info.get_cost() for m in self._modules)

    def set_verbose(self, flag):
        self._verbose = flag
        self._logger.set_echo(LogSource.MODULE, flag)
        self._logger.set_echo(LogSource.ENV, flag)

    def get_logger(self):
        return self._logger

    def log(self, source, text):
        return self._logger.log(source, text)

    def get_journal(self):
        return list(self._journal)

    def count_events(self, event_type):
        return sum(1 for event in self._journal if event.type == event_type)

    # окружение 

    def set_environment(self, environment):
        if self._current_environment is not None:
            for module in self.get_modules():
                self._current_environment.revert_effect(module)
        if not isinstance(environment, EnvironmentProxy):
            environment = EnvironmentProxy(environment)
        environment.set_logger(self._logger)
        self._current_environment = environment
        self.log(LogSource.CENTER, f"окружение: {environment.get_name()}")

    def get_environment(self):
        return self._current_environment

    def get_environment_name(self):
        if self._current_environment is None:
            return "не задано"
        return self._current_environment.get_name()

    def get_energy_modifier(self):
        if self._current_environment is None:
            return 1.0
        return self._current_environment.get_energy_modifier()

    def get_damage_factor(self):
        modifier = 1.0
        if self._current_environment is not None:
            modifier = self._current_environment.get_damage_modifier()
        return modifier * self.get_resistance()

    def apply_environment(self):
        if self._current_environment is None:
            return
        for module in self.get_modules():
            self._current_environment.apply_effect(module)

    def get_total_consumption(self):
        total = 0
        for module in self._modules:
            if module.active:
                total += module.get_energy_usage(self.get_energy_modifier())
        return total

    def tick(self):
        energy_used = 0
        oxygen_used = 0
        for module in self.get_modules():
            if module.active:
                energy_used += module.consume_energy(self.get_energy_modifier())
                oxygen_used += module.get_oxygen_usage()
        used = ResourcePackage(min(energy_used, self._energy), min(oxygen_used, self._oxygen))
        self -= ResourcePackage(energy_used, oxygen_used)

        if self._energy == 0:
            self.log(LogSource.CENTER, "ВНИМАНИЕ: энергия закончилась, модули отключаются")
            for module in self.get_modules():
                module.deactivate()
        if self._oxygen == 0 and oxygen_used > 0:
            self.log(LogSource.CENTER, "ВНИМАНИЕ: кислород закончился")

        self.apply_environment()
        return used

    # внешние объекты 

    def handle_external_object(self, external_object):
        self.log(LogSource.CENTER, f"внешний объект: {external_object.get_name()}")
        external_object.affect_station(self)

    # перегрузка операций 

    def add_resources(self, package):
        self._energy += package.get_energy()
        self._oxygen += package.get_oxygen()
        self._safety_level = min(100, self._safety_level + package.get_safety_level())

    def consume_resources(self, package):
        self._energy = max(0, self._energy - package.get_energy())
        self._oxygen = max(0, self._oxygen - package.get_oxygen())
        self._safety_level = max(0, self._safety_level - package.get_safety_level())

    def scale_energy(self, factor):
        if factor < 0:
            raise ValueError("Множитель не может быть отрицательным")
        self._energy = int(self._energy * factor + 0.5)

    def __add__(self, package):
        if not isinstance(package, ResourcePackage):
            return NotImplemented
        self.add_resources(package)
        return self

    def __sub__(self, package):
        if not isinstance(package, ResourcePackage):
            return NotImplemented
        self.consume_resources(package)
        return self

    def __mul__(self, factor):
        if isinstance(factor, bool) or not isinstance(factor, (int, float)):
            return NotImplemented
        self.scale_energy(factor)
        return self

    # Наблюдатель 

    def on_module_event(self, event):
        self._journal.append(event)
        self.log(LogSource.MODULE, str(event))

        module = self.find_module(event.module_id)
        if module is None:
            return

        if event.type == EventType.DAMAGED:
            self._total_damage += event.damage
            self._safety_level = max(0, self._safety_level - DAMAGE_SAFETY_PENALTY)
            self._update_critical(module)
        elif event.type == EventType.DESTROYED:
            self.remove_module_by_id(module.id)
            self.log(LogSource.CENTER, f"модуль '{module.name}' уничтожен и удалён со станции")
        elif event.type == EventType.REPAIR:
            self._update_critical(module)
        elif event.type == EventType.STATE_CHANGED and module.state == "авария":
            self._safety_level = max(0, self._safety_level - 5)
            self.log(LogSource.CENTER, f"АВАРИЯ модуля '{module.name}', "
                                       f"уровень безопасности снижен до {self._safety_level}")

    def _update_critical(self, module):
        ratio = module.durability.get_value() / module.durability.get_max()
        if ratio < CRITICAL_RATIO and module.id not in self._critical:
            self._critical.add(module.id)
            self.log(LogSource.CENTER, f"ВНИМАНИЕ: модуль '{module.name}' в критическом состоянии "
                                       f"(прочность {module.durability.get_value()}/"
                                       f"{module.durability.get_max()})")
        elif ratio >= CRITICAL_RATIO and module.id in self._critical:
            self._critical.discard(module.id)
            self.log(LogSource.CENTER, f"модуль '{module.name}' вышел из критического состояния")

    def __str__(self):
        return (f"Командный центр | модулей: {len(self)}/{self.get_max_modules()} | "
                f"энергия: {self._energy} | кислород: {self._oxygen} | "
                f"безопасность: {self._safety_level} | окружение: {self.get_environment_name()}")
