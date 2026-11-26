# Паттерн "Абстрактная фабрика" для создания модулей
from abc import ABC, abstractmethod

from modules import (CrewCabin, MedicalCabin, SolarModule, ReactorModule,
                     BiologyLab, PhysicsLab)


class ModuleFactory(ABC):
    """Интерфейс фабрики"""

    @abstractmethod
    def create_residential_module(self, name, efficiency=100):
        pass

    @abstractmethod
    def create_energy_module(self, name, efficiency=100):
        pass

    @abstractmethod
    def create_research_module(self, name, efficiency=100):
        pass


class StandardModuleFactory(ModuleFactory):
    """Фабрика стандартных модулей"""

    def create_residential_module(self, name, efficiency=100):
        return CrewCabin(name, efficiency)

    def create_energy_module(self, name, efficiency=100):
        return SolarModule(name, efficiency)

    def create_research_module(self, name, efficiency=100):
        return BiologyLab(name, efficiency)


class AdvancedModuleFactory(ModuleFactory):
    """Фабрика улучшенных модулей"""

    def create_residential_module(self, name, efficiency=100):
        return MedicalCabin(name, efficiency)

    def create_energy_module(self, name, efficiency=100):
        return ReactorModule(name, efficiency)

    def create_research_module(self, name, efficiency=100):
        return PhysicsLab(name, efficiency)
