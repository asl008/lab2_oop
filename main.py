import random

from command_center import CommandCenter
from damage import Damage, IMPACT
from environment import EarthOrbit, DeepSpace, AsteroidField
from external_objects import SolarStorm, MeteorShower, CargoContainer, SpaceAnomaly
from factory import StandardModuleFactory, AdvancedModuleFactory
from logging_proxy import LogSource
from modules import Module, ResidentialModule
from observer import EventType
from resource_package import ResourcePackage
from strategies import StrategyContext, DefaultStrategy, ReactorModuleStrategy
from type_info import ModuleTypeInfoFactory


def print_center(center, title):
    print(title)
    print(" ", center)
    for module in center:
        print("   ", module)
    print()


def build_center():
    Module.reset_ids()
    center = CommandCenter(max_modules=8, energy=1000, oxygen=500, safety_level=50)
    standard = StandardModuleFactory()
    advanced = AdvancedModuleFactory()

    center.create_module(standard, "residential", "Кабина-1", 90)
    center.create_module(standard, "energy", "Солнце-1", 80)
    center.create_module(standard, "research", "Био-1", 70)
    center.create_module(advanced, "residential", "Медблок-1", 95)
    center.create_module(advanced, "energy", "Реактор-1", 100)
    center.create_module(advanced, "research", "Физика-1", 85)
    return center


def find_by_name(center, name):
    for module in center:
        if module.name == name:
            return module
    return None


def scenario_1():
    print("=== Сценарий 1: создание центра, добавление модулей, установка окружения ===")
    Module.reset_ids()
    center = CommandCenter(max_modules=7, energy=1000, oxygen=500, safety_level=50)
    standard = StandardModuleFactory()
    advanced = AdvancedModuleFactory()

    center.create_module(standard, "residential", "Кабина-1", 90)
    center.create_module(standard, "energy", "Солнце-1", 80)
    center.create_module(advanced, "research", "Физика-1", 85)
    cabin2 = center.create_module(standard, "residential", "Кабина-2", 100)
    print_center(center, "Центр после добавления модулей:")

    cabin1 = find_by_name(center, "Кабина-1")
    print("Общий объект типа у Кабина-1 и Кабина-2:", cabin1.type_info is cabin2.type_info)
    print("Создано объектов-легковесов:", ModuleTypeInfoFactory.count(), "(модулей на станции:", len(center), ")")
    print("Общая стоимость модулей:", center.get_total_cost())
    print()

    center.set_environment(EarthOrbit())
    for module in center:
        module.activate()
    used = center.tick()
    print("Такт на орбите Земли, потрачено:", used)
    print_center(center, "Состояние после такта:")

    # ограничение размера станции
    center.create_module(advanced, "energy", "Реактор-1", 100)
    center.create_module(advanced, "residential", "Медблок-1", 95)
    center.create_module(standard, "research", "Био-1", 70)
    try:
        center.create_module(standard, "energy", "Лишний", 100)
    except ValueError as e:
        print("Ошибка:", e)
    try:
        center.create_module(standard, "garden", "Оранжерея", 100)
    except ValueError as e:
        print("Ошибка:", e)
    print()


def scenario_2():
    print("=== Сценарий 2: смена окружения на DeepSpace, прокси и уведомления центра ===")
    center = build_center()
    for module in center:
        module.activate()
    find_by_name(center, "Медблок-1").set_state("ремонт")
    find_by_name(center, "Реактор-1").set_state("авария")
    print()

    center.set_environment(EarthOrbit())
    print("Потребление за такт (Орбита Земли):", center.get_total_consumption(), "кВт")
    center.tick()
    print()

    center.set_environment(DeepSpace())
    print("Потребление за такт (x1.5):", center.get_total_consumption(), "кВт")
    safety_before = center.get_safety_level()
    center.tick()
    center.tick()
    print_center(center, "После двух тактов в глубоком космосе:")
    print("Уведомления центра: повреждений", center.count_events(EventType.DAMAGED),
          ", расход энергии", center.count_events(EventType.ENERGY_CONSUMED),
          ", безопасность", safety_before, "->", center.get_safety_level())
    print()

    center.set_environment(AsteroidField())
    center.tick()
    print_center(center, "Астероидное поле: исследовательские модули заблокированы:")
    center.tick()

    proxy = center.get_environment()
    print("Журнал прокси (последние записи):")
    for line in proxy.get_log()[-6:]:
        print(" ", line)
    print("Применено:", proxy.get_applied_count(), "пропущено:", proxy.get_skipped_count())
    bio = find_by_name(center, "Био-1")
    print("Результат из кеша прокси для Био-1:", proxy.get_cached_result(bio))
    print("Обращений к кешу модификаторов:", proxy.get_cache_hits())
    logger = center.get_logger()
    print("Записей журнала:", {source.value: logger.count(source) for source in LogSource})
    print()

    center.set_environment(EarthOrbit())
    for module in center:
        if module.get_category() == "research":
            print(f"  {module.name}: состояние {module.state}")
    print()


def scenario_3():
    print("=== Сценарий 3: паттерн Стратегия - солнечная буря и разные типы модулей ===")
    center = build_center()
    center.set_environment(EarthOrbit())
    print()

    before = {m.id: (m.durability.get_value(), m.efficiency) for m in center}
    center.set_verbose(True)
    print("Уведомления центра (буря применяет module -= Damage через стратегию типа модуля):")
    center.handle_external_object(SolarStorm(power=20))
    center.set_verbose(False)
    print()

    print("Результат (одна и та же буря, разные стратегии):")
    for module in center:
        dur, eff = before[module.id]
        print(f"  {module.name:10} ({module.get_type():13}) прочность {dur:3} -> "
              f"{module.durability.get_value():3}, эффективность {eff:3}% -> {module.efficiency:3}%, "
              f"состояние: {module.state}")
    print("Энергия центра после сбоя электроники:", center.get_energy(), ", безопасность:",
          center.get_safety_level(), ", суммарный урон:", center.get_total_damage())
    print()

    # та же буря в глубоком космосе сильнее
    center.set_environment(DeepSpace())
    print("Множитель урона в глубоком космосе:", center.get_environment().get_damage_modifier())
    reactor = find_by_name(center, "Реактор-1")
    before_value = reactor.durability.get_value()
    center.handle_external_object(SolarStorm(power=20))
    print(f"Реактор-1: прочность {before_value} -> {reactor.durability.get_value()}, "
          f"состояние: {reactor.state}")
    print()


def scenario_4():
    print("=== Сценарий 4: грузовой контейнер - полезное воздействие ===")
    center = build_center()
    center.set_environment(EarthOrbit())
    solar = find_by_name(center, "Солнце-1")
    solar -= Damage(40, IMPACT)
    print()

    print("До:", center)
    print("До:", solar)
    center.handle_external_object(CargoContainer(energy=150, oxygen=80, repair=15, safety_level=5))
    print("После:", center)
    print("После:", solar)
    print()

    print("--- Операция + для модуля ---")
    reactor = find_by_name(center, "Реактор-1")
    print("До:", reactor)
    reactor += ResourcePackage(energy=40)
    print("reactor += ResourcePackage(energy=40):", reactor)
    print()


def scenario_5():
    print("=== Сценарий 5: внешние объекты и перегрузка операций ===")
    center = build_center()
    center.set_environment(EarthOrbit())
    print()

    print("--- Операции (+, -, *) ---")
    print("До:", center)
    center += ResourcePackage(energy=100, oxygen=50)
    print("center += ResourcePackage(100, 50):", center)
    center -= ResourcePackage(energy=30, oxygen=10)
    print("center -= ResourcePackage(30, 10):  ", center)
    center *= 1.5
    print("center *= 1.5 (энергия):            ", center)
    print()

    bio = find_by_name(center, "Био-1")
    print("До:", bio)
    bio -= Damage(25, IMPACT)
    print("bio -= Damage(25):", bio)
    bio *= 1.2
    print("bio *= 1.2 (эффективность):", bio)
    bio += ResourcePackage(energy=10)
    print("bio += ResourcePackage(10) (заряд):", bio)
    print()

    print("--- Именованные методы (то же самое) ---")
    bio.apply_damage(Damage(5, IMPACT))
    bio.scale_efficiency(1.1)
    bio.add_resources(ResourcePackage(energy=5))
    center.add_resources(ResourcePackage(energy=10))
    center.consume_resources(ResourcePackage(energy=10))
    center.scale_energy(1.0)
    print(bio)
    try:
        center + 5
    except TypeError as e:
        print("Неподдерживаемый тип:", e)
    print()

    print("--- Метеоритный поток ---")
    center.handle_external_object(MeteorShower(hits=3, rng=random.Random(5)))
    print()

    print("--- Космическая аномалия ---")
    anomaly = SpaceAnomaly(rng=random.Random(4))
    for _ in range(6):
        center.handle_external_object(anomaly)
    print_center(center, "Состояние после всех воздействий:")


def scenario_6():
    print("=== Сценарий 6: паттерн Наблюдатель - уведомления командного центра ===")
    center = build_center()
    center.set_verbose(True)
    solar = find_by_name(center, "Солнце-1")
    print()

    print("--- Активация, расход и изменение потребления ---")
    solar.activate()
    solar.consume_energy()
    solar.set_energy_consumption(8)
    print()

    print("--- Повреждения ---")
    solar -= Damage(30, IMPACT)
    solar -= Damage(35, IMPACT)  
    print("Уровень безопасности:", center.get_safety_level())
    print()

    print("--- Ремонт ---")
    solar.set_state("ремонт")
    solar.repair(40)
    solar.set_state("включён")
    print()

    print("--- Уничтожение: центр удаляет модуль из списка ---")
    print("Модулей до:", len(center))
    solar -= Damage(500, IMPACT)
    print("Модулей после:", len(center), ", модуль на станции:", center.find_module(solar.id))
    print("Уровень безопасности:", center.get_safety_level())
    print()

    center.set_verbose(False)
    print("Всего событий в журнале центра:", len(center.get_journal()))
    for event_type in EventType:
        count = center.count_events(event_type)
        if count > 0:
            print(f"  {event_type.value}: {count}")
    print("Суммарный урон, учтённый центром:", center.get_total_damage())
    print()

    print("--- Подписка и отписка ---")
    bio = find_by_name(center, "Био-1")
    journal_size = len(center.get_journal())
    bio.unsubscribe(center)
    bio -= Damage(10, IMPACT)
    print("Событий после отписки:", len(center.get_journal()) - journal_size)
    bio.subscribe(center)
    bio -= Damage(10, IMPACT)
    print("Событий после повторной подписки:", len(center.get_journal()) - journal_size)
    print()


class Greenhouse(ResidentialModule):
    """Новый тип модуля: добавлен только здесь, командный центр и стратегии не менялись"""

    def __init__(self, name, efficiency=None):
        info = ModuleTypeInfoFactory.get("Greenhouse", max_durability=90, base_energy=15,
                                         capacity=6, max_charge=40, cost=500)
        super().__init__(name, info, efficiency)


def scenario_7():
    print("=== Сценарий 7: взаимодействие модулей, расширяемость и замена стратегий ===")
    center = build_center()
    reactor = find_by_name(center, "Реактор-1")
    physics = find_by_name(center, "Физика-1")
    bio = find_by_name(center, "Био-1")

    print(f"Заряд до: {reactor.name} {reactor.charge.get_value()}/{reactor.charge.get_max()}, "
          f"{physics.name} {physics.charge.get_value()}/{physics.charge.get_max()}")
    moved = reactor.transfer_energy(physics, 30)
    print(f"Передано {moved}: {reactor.name} {reactor.charge.get_value()}, "
          f"{physics.name} {physics.charge.get_value()}")

    moved = reactor.transfer_energy(physics, 100)
    print(f"Передано {moved}: {reactor.name} {reactor.charge.get_value()}, "
          f"{physics.name} {physics.charge.get_value()}/{physics.charge.get_max()}")

    center.set_verbose(True)
    bio.set_state("ремонт")
    reactor.transfer_energy(bio, 10)
    center.set_verbose(False)

    try:
        reactor.transfer_energy(reactor, 10)
    except ValueError as e:
        print("Ошибка:", e)
    print()

    greenhouse = Greenhouse("Оранжерея-1", 90)
    center.add_module(greenhouse)
    greenhouse.activate()
    print("Добавлен новый тип:", greenhouse)
    center.set_environment(EarthOrbit())
    center.handle_external_object(SolarStorm(power=20))
    print("После солнечной бури:", greenhouse)
    print()

    print("--- Взаимозаменяемые стратегии ---")
    custom = StrategyContext()
    custom.register(Module, DefaultStrategy())
    custom.register(ResidentialModule, ReactorModuleStrategy())
    spare = Greenhouse("Оранжерея-2", 90)
    custom.apply(spare, Damage(20, IMPACT))
    print("Жилой модуль со стратегией реактора (урон x0.5):", spare.durability.get_value(), "/",
          spare.durability.get_max())
    custom.register(ResidentialModule, DefaultStrategy())
    custom.apply(spare, Damage(20, IMPACT))
    print("После замены на стратегию по умолчанию (урон x1):", spare.durability.get_value(), "/",
          spare.durability.get_max())
    print()


def scenario_8():
    print("=== Сценарий 8: обход, ссылки и копии ===")
    empty = CommandCenter(max_modules=3)
    print("Обход пустого центра:", list(empty))

    center = build_center()
    first = iter(center)
    second = iter(center)
    print("Первый итератор:", next(first).name, next(first).name)
    print("Второй итератор (независимый):", next(second).name)
    names = [m.name for m in center]
    print("Полный обход:", names)

    center.remove_module_by_index(0)
    print("Старый итератор обходит снимок, а новый - текущее состояние:",
          len(list(first)), "и", len(list(iter(center))))
    print()

    cabin = find_by_name(center, "Медблок-1")
    alias = cabin
    alias -= Damage(10, IMPACT)
    print("Присваивание - вторая ссылка на тот же объект:", alias is cabin,
          ", прочность", cabin.durability.get_value())

    copy_of_cabin = cabin.clone()
    copy_of_cabin -= Damage(20, IMPACT)
    print("clone() - независимая копия:", copy_of_cabin is not cabin,
          ", прочность копии", copy_of_cabin.durability.get_value(),
          ", оригинала", cabin.durability.get_value())
    print("У копии новый id:", copy_of_cabin.id != cabin.id,
          ", подписки не копируются:", copy_of_cabin._observers == [],
          ", легковес общий:", copy_of_cabin.type_info is cabin.type_info)
    print()


def main():
    scenario_1()
    scenario_2()
    scenario_3()
    scenario_4()
    scenario_5()
    scenario_6()
    scenario_7()
    scenario_8()


if __name__ == "__main__":
    main()
