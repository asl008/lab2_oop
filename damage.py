RADIATION = "радиация"
IMPACT = "удар"


class Damage:
    """Урон"""

    def __init__(self, amount, type_=IMPACT):
        if amount < 0:
            raise ValueError("Урон не может быть отрицательным")
        self.__amount = amount
        self.__type = type_

    def get_amount(self):
        return self.__amount

    def get_type(self):
        return self.__type

    def scaled(self, factor):
        if factor < 0:
            raise ValueError("Коэффициент не может быть отрицательным")
        return Damage(int(self.__amount * factor + 0.5), self.__type)

    def __str__(self):
        return f"{self.__amount} ({self.__type})"
