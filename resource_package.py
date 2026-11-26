class ResourcePackage:
    """Набор ресурсов: энергия, кислород и уровень безопасности"""

    def __init__(self, energy=0, oxygen=0, safety_level=0):
        if energy < 0 or oxygen < 0 or safety_level < 0:
            raise ValueError("Количество ресурсов не может быть отрицательным")
        self.__energy = energy
        self.__oxygen = oxygen
        self.__safety_level = safety_level

    def get_energy(self):
        return self.__energy

    def get_oxygen(self):
        return self.__oxygen

    def get_safety_level(self):
        return self.__safety_level

    def __str__(self):
        text = f"энергия: {self.__energy}, кислород: {self.__oxygen}"
        if self.__safety_level > 0:
            text += f", безопасность: {self.__safety_level}"
        return text
