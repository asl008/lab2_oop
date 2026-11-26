from dataclasses import dataclass

from environment import Environment
from logging_proxy import LogSource


@dataclass(frozen=True)
class EffectResult:
    """Результат применения эффекта к модулю, неизменяемая запись кеша прокси"""
    module_id: int
    durability_before: int
    durability_after: int
    state: str
    applied: bool


class EnvironmentProxy(Environment):
    """Прокси окружения"""

    def __init__(self, real_environment):
        super().__init__()
        self._real_environment = real_environment
        self._applied = 0
        self._skipped = 0
        self._results = {}  
        self._modifiers = {}  
        self._cache_hits = 0

    def get_real_environment(self):
        return self._real_environment

    def set_logger(self, logger):
        super().set_logger(logger)
        self._real_environment.set_logger(logger)

    def get_name(self):
        return self._real_environment.get_name()

    def get_energy_modifier(self):
        return self._cached_modifier("energy", self._real_environment.get_energy_modifier)

    def get_damage_modifier(self):
        return self._cached_modifier("damage", self._real_environment.get_damage_modifier)

    def blocks_research(self):
        return self._real_environment.blocks_research()

    def apply_effect(self, module):
        if module.state == "авария":
            self._skip(module, f"'{module.name}' в аварии - эффект не применяется")
            return

        if module.state == "ремонт":
            self._skip(module, f"'{module.name}' на ремонте (защищён) - эффект не применяется")
            return

        if module.get_category() == "research":
            if self.blocks_research() and module.state == "заблокирован":
                self._skip(module, f"'{module.name}' исследовательский модуль уже заблокирован "
                                   f"окружением - эффект не применяется")
                return
            self._write(f"'{module.name}': исследовательский модуль, проверка допуска пройдена")

        before = module.durability.get_value()
        self._real_environment.apply_effect(module)
        after = module.durability.get_value()
        self._results[module.id] = EffectResult(module.id, before, after, module.state, True)
        self._write(f"'{module.name}': эффект применён, прочность {before} -> {after}, "
                    f"состояние: {module.state}")
        self._applied += 1

    def revert_effect(self, module):
        self._real_environment.revert_effect(module)
        self._write(f"'{module.name}': эффекты окружения сняты, состояние: {module.state}")

    def get_log(self):
        return [str(entry) for entry in self._logger.get_entries(LogSource.ENV)]

    def get_applied_count(self):
        return self._applied

    def get_skipped_count(self):
        return self._skipped

    # кеширование

    def get_cached_result(self, module):
        return self._results.get(module.id)

    def get_cache_hits(self):
        return self._cache_hits

    def clear_cache(self):
        self._results = {}
        self._modifiers = {}

    def _cached_modifier(self, key, getter):
        if key in self._modifiers:
            self._cache_hits += 1
        else:
            self._modifiers[key] = getter()
        return self._modifiers[key]

    def _skip(self, module, text):
        durability = module.durability.get_value()
        self._results[module.id] = EffectResult(module.id, durability, durability, module.state, False)
        self._write(text)
        self._skipped += 1

    def _write(self, text):
        self._logger.log(LogSource.ENV, f"[Прокси: {self.get_name()}] {text}")
