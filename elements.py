from dataclasses import dataclass

@dataclass(frozen=True, eq=True)
class Element:
    name: str
    symbol: str
    molar_mass: int

    @property
    def full_name(self):
        return f"{self.name} ({self.symbol})"


class NonExistentElementException(Exception):
    pass


elements = [
    Element("Hydrogen", "H", 1.0078),
    Element("Helium", "He", 4.0026),
    Element("Lithium", "Li", 6.941),
    Element("Beryllium", "Be", 9.0122),
    Element("Boron", "B", 10.811),
    Element("Carbon", "C", 12.0107),
    Element("Nitrogen", "N", 14.0067),
    Element("Oxygen", "O", 15.9994),
    Element("Fluorine", "F", 18.9984),
    Element("Neon", "Ne", 20.1797),
    Element("Sodium", "Na", 22.9897),
    Element("Magnesium", "Mg", 24.305),
    Element("Aluminium", "Al", 28.0855),
    Element("Silicon", "Si", 28.0855),
    Element("Phosphorus", "P", 30.9738),
    Element("Sulfur", "S", 32.065),
    Element("Chlorine", "Cl", 35.453),
    Element("Argon", "Ar", 39.948),
    Element("Potassium", "K", 39.0983),
    Element("Calcium", "Ca", 40.078),
    Element("Scandium", "Sc", 44.9559),
    Element("Titanium", "Ti", 47.867),
    Element("Vanadium", "V", 50.9415),
    Element("Chromium", "Cr", 51.9961),
    Element("Manganese", "Mn", 54.938),
    Element("Iron", "Fe", 55.845),
    Element("Cobalt", "Co", 58.9332),
    Element("Nickel", "Ni", 58.6934),
    Element("Copper", "Cu", 63.546),
    Element("Zinc", "Zn", 65.39),
    Element("Gallium", "Ga", 69.723),
    Element("Germanium", "Ge", 72.64),
    Element("Bromine", "Br", 79.904),
    Element("Krypton", "Kr", 83.8),
    Element("Rubidium", "Rb", 85.4678),
    Element("Strontium", "Sr", 87.62),
    Element("Zirconium", "Zr", 91.224),
    Element("Niobium", "Nb", 92.9064),
    Element("Molybdenum", "Mo", 95.94),
    Element("Silver", "Ag", 107.8682),
    Element("Cadmium", "Cd", 112.411),
    Element("Indium", "In", 114.818),
    Element("Tin", "Sn", 118.71),
    Element("Iodine", "I", 121.76),
    Element("Xenon", "Xe", 131.293),
    Element("Cesium", "Cs", 132.9055),
    Element("Barium", "Ba", 137.327),
    Element("Tantalum", "Ta", 180.9470),
    Element("Tungsten", "W", 183.84),
    Element("Lead", "Pb", 207.2),
    Element("Radon", "Rn", 222),
    Element("Thorium", "Th", 232.0381),
    Element("Uranium", "U", 238.0289),
]

element_names = list(map(lambda el : el.full_name, elements))
element_symbols = list(map(lambda el : el.symbol, elements))

def get_element_by_name(name: str):
    for el in elements:
        if el.name == name:
            return el
        if el.full_name == name:
            return el
        if el.symbol == name:
            return el
    
    raise NonExistentElementException("Could not find element")