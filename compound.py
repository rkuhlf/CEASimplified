from mimetypes import init
import re
from wsgiref.handlers import format_date_time

from Exceptions import UserInputException


class Compound:
    pass

class PresetCompound(Compound):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
    
class CustomCompound(Compound):
    """Represents the information about a compound that is not a preset"""
    def __init__(self, name: str, formation_heat: float, elements: dict) -> None:
        self.name = name
        self.formation_heat = formation_heat
        self.elements = elements
    
    def elements_string(self) -> str:
        "Returns a string representation of the elements"
        
        if len(self.elements) == 0:
            raise UserInputException("Elements must be added for both the oxidizer and fuel inputs.")

        ans = ""
        for (element, amount) in self.elements.items():
            symbol = re.search("\((.*)\)", element).groups()[0]
            ans += symbol + " " + str(amount) + " "

        return ans
