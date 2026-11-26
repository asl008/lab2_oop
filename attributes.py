class Durability:
    """Прочность модуля"""

    def __init__(self, value, max_value=100):
        if max_value < 0:
            raise ValueError("Максимальная прочность не может быть отрицательной")
        self.__max_value = max_value
        self.__value = 0
        self.set_value(value)

    def get_value(self):
        return self.__value

    def get_max(self):
        return self.__max_value

    def set_value(self, new_value):
        if new_value < 0:
            raise ValueError("Прочность не может быть отрицательной")
        if new_value > self.__max_value:
            raise ValueError("Прочность не может быть выше максимума")
        self.__value = new_value

    def decrease(self, amount):
        if amount < 0:
            raise ValueError("Значение должно быть положительным")
        self.__value = max(0, self.__value - amount)

    def repair(self, amount):
        if amount < 0:
            raise ValueError("Значение должно быть положительным")
        self.__value = min(self.__max_value, self.__value + amount)


class EnergyConsumption:
    """Энергопотребление модуля"""

    def __init__(self, value):
        self.__value = 0
        self.set_value(value)

    def get_value(self):
        return self.__value

    def set_value(self, new_value):
        if new_value < 0:
            raise ValueError("Энергопотребление не может быть отрицательным")
        self.__value = new_value

    def increase(self, amount):
        if amount < 0:
            raise ValueError("Значение должно быть положительным")
        self.__value += amount

    def decrease(self, amount):
        if amount < 0:
            raise ValueError("Значение должно быть положительным")
        self.__value = max(0, self.__value - amount)


class Capacity:
    """Вместимость модуля"""

    def __init__(self, value):
        self.__value = 0
        self.set_value(value)

    def get_value(self):
        return self.__value

    def set_value(self, new_value):
        if new_value < 0:
            raise ValueError("Вместимость не может быть отрицательной")
        self.__value = new_value


class EnergyCharge:
    """Заряд модуля"""

    def __init__(self, value, max_value=100):
        if max_value < 0:
            raise ValueError("Максимальный заряд не может быть отрицательным")
        self.__max_value = max_value
        self.__value = 0
        self.set_value(value)

    def get_value(self):
        return self.__value

    def get_max(self):
        return self.__max_value

    def set_value(self, new_value):
        if new_value < 0:
            raise ValueError("Заряд не может быть отрицательным")
        if new_value > self.__max_value:
            raise ValueError("Заряд не может быть выше максимума")
        self.__value = new_value

    def add(self, amount):
        if amount < 0:
            raise ValueError("Значение должно быть положительным")
        accepted = min(amount, self.__max_value - self.__value)
        self.__value += accepted
        return accepted

    def take(self, amount):
        if amount < 0:
            raise ValueError("Значение должно быть положительным")
        taken = min(amount, self.__value)
        self.__value -= taken
        return taken
