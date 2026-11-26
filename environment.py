from abc import ABC, abstractmethod

from damage import Damage, RADIATION, IMPACT
from logging_proxy import LoggingProxy, LogSource
from strategies import default_context


class Environment(ABC):
    """Интерфейс космического окружения"""

    def __init__(self):
        self._logger = LoggingProxy(echo=())

    def set_logger(self, logger):
        self._logger = logger

    def _log(self, text):
        self._logger.log(LogSource.ENV, f"{self.get_name()}: {text}")

    @abstractmethod
    def apply_effect(self, module):
        """Применить влияние окружения к модулю"""
        pass

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_energy_modifier(self):
        """Множитель расхода энергии"""
        pass

    @abstractmethod
    def get_damage_modifier(self):
        """Множитель урона от внешних воздействий"""
        pass

    def blocks_research(self):
        return False

    def revert_effect(self, module):
        pass


class EarthOrbit(Environment):
    """Орбита Земли умеренное окружение, низкий риск"""

    def get_name(self):
        return "Орбита Земли"

    def get_energy_modifier(self):
        return 1.0

    def get_damage_modifier(self):
        return 1.0

    def apply_effect(self, module):
        self._log(f"'{module.name}': влияние минимально, эффект нейтральный")


class DeepSpace(Environment):
    """Глубокий космос энергопотребление x1.5 и периодическое радиационное облучение"""

    RADIATION_POWER = 4

    def __init__(self, strategies=None):
        super().__init__()
        if strategies is None:
            strategies = default_context()
        self._strategies = strategies

    def get_name(self):
        return "Глубокий космос"

    def get_energy_modifier(self):
        return 1.5

    def get_damage_modifier(self):
        return 1.5

    def apply_effect(self, module):
        damage = Damage(self.RADIATION_POWER, RADIATION).scaled(self.get_damage_modifier())
        self._strategies.apply(module, damage)


class AsteroidField(Environment):
    """Астероидное поле: высокий риск, исследовательские модули блокируются"""

    IMPACT_POWER = 3

    def __init__(self, strategies=None):
        super().__init__()
        if strategies is None:
            strategies = default_context()
        self._strategies = strategies

    def get_name(self):
        return "Астероидное поле"

    def get_energy_modifier(self):
        return 1.0

    def get_damage_modifier(self):
        return 2.0

    def blocks_research(self):
        return True

    def apply_effect(self, module):
        damage = Damage(self.IMPACT_POWER, IMPACT).scaled(self.get_damage_modifier())
        self._strategies.apply(module, damage)
        if module.get_category() == "research" and module.state == "включён":
            module.set_state("заблокирован")

    def revert_effect(self, module):
        if module.get_category() == "research" and module.state == "заблокирован":
            module.set_state("включён")
