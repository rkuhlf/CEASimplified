


import tkinter as tk
from tkinter import ttk
from typing import List


class SearchableDropdown(tk.Frame):
    def check_input(self, event):
        value = event.widget.get()

        if value == '':
            self.combo_box['values'] = self.items
        else:
            data = []
            for item in self.items:
                if value.lower() in item.lower():
                    data.append(item)

            self.combo_box['values'] = data

    
    def __init__(self, parent, items: "List[str]"=[]):
        super(SearchableDropdown, self).__init__(parent)

        self.items = items

        self.combo_box = ttk.Combobox(self)
        self.combo_box['values'] = items
        self.combo_box.bind('<KeyRelease>', self.check_input)
        self.combo_box.pack()
    
    @property
    def value(self):
        return self.combo_box.get()
    
    @value.setter
    def value(self, v) -> None:
        self.combo_box.set(v)


# TODO: go through and delete all of the ones that CEA rejects
elements = [
    "Hydrogen (H)",
    "Helium (He)",
    "Lithium (Li)",
    "Beryllium (Be)",
    "Boron (B)",
    "Carbon (C)",
    "Nitrogen (N)",
    "Oxygen (O)",
    "Fluorine (F)",
    "Neon (Ne)",
    "Sodium (Na)",
    "Magnesium (Mg)",
    "Aluminium (Al)",
    "Silicon (Si)",
    "Phosphorus (P)",
    "Sulfur (S)",
    "Chlorine (Cl)",
    "Argon (Ar)",
    "Potassium (K)",
    "Calcium (Ca)",
    "Scandium (Sc)",
    "Titanium (Ti)",
    "Vanadium (V)",
    "Chromium (Cr)",
    "Manganese (Mn)",
    "Iron (Fe)",
    "Cobalt (Co)",
    "Nickel (Ni)",
    "Copper (Cu)",
    "Zinc (Zn)",
    "Gallium (Ga)",
    "Germanium (Ge)",
    "Bromine (Br)",
    "Krypton (Kr)",
    "Rubidium (Rb)",
    "Strontium (Sr)",
    "Zirconium (Zr)",
    "Niobium (Nb)",
    "Molybdenum (Mo)",
    "Silver (Ag)",
    "Cadmium (Cd)",
    "Indium (In)",
    "Tin (Sn)",
    "Iodine (I)",
    "Xenon (Xe)",
    "Cesium (Cs)",
    "Barium (Ba)",
    "Tantalum (Ta)",
    "Tungsten (W)",
    "Lead (Pb)",
    "Radon (Rn)",
    "Thorium (Th)",
    "Uranium (U)",
]

class ElementDropDown(tk.Frame):
    def __init__(self, parent):
        super(ElementDropDown, self).__init__(parent)

        self.elementDropDown = SearchableDropdown(self, elements)
        self.elementDropDown.pack()

    @property
    def element(self) -> str:
        current: str = self.elementDropDown.value
        
        if current in elements:
            return current

        return ""
    
    @element.setter
    def element(self, new_element) -> None:
        self.elementDropDown.value = new_element
