import tkinter as tk
from turtle import width
from typing import Dict, List
import typing

from elements import Element, NonExistentElementException, element_names, elements, get_element_by_name
from ElementDropDown import ElementDropDown, SearchableDropdown
from Exceptions import PresetException, UserInputException
from helperWidgets import LabeledInput, NumericalEntry, NumericalEntryWithUnits, help_button
from fonts import title_font, subtitle_font


class MolarMassMultiplier:
    def __init__(self, multiplier=1, power=1) -> None:
        self.multiplier = multiplier
        self.power = power
    
    def calculate_multiplier(self, elements: Dict[Element, float]) -> float:
        """Takes a dictionary of elements and returns the molar mass raised to the power specified on initialization"""
        total = 0
        for element, amount in elements.items():
            total += element.molar_mass * amount
        
        return self.multiplier * total ** self.power

class InputMolarMassUnits(NumericalEntryWithUnits):
    @property
    def base_value(self) -> float:
        raise Exception("Cannot get the base value of units that include molar mass without knowing the element breakdown. Use get_base_value instead")

    def get_base_value(self, elements: Dict[Element, str]):
        conversion = self.unit_conversions.get(self.units)
        
        if isinstance(conversion, MolarMassMultiplier):
            conversion = conversion.calculate_multiplier(elements)
        print(conversion)
        return float(self.value) / conversion
    
    

class ElementDictionaryPair(tk.Frame):
    def __init__(self, parent, delete_function, id: int, element="", amount="") -> None:
        super(ElementDictionaryPair, self).__init__(parent)

        self.id: int = id
        self.delete_function = delete_function

        self.input_frame = tk.Frame(self)
        self.input_frame.pack(side=tk.LEFT)

        self.element_input = ElementDropDown(self.input_frame)
        self.element_input.element = element
        self.element_input.pack(side=tk.LEFT)

        self.amount_input = NumericalEntry(self.input_frame, width=8)
        self.amount_input.delete(0, tk.END)
        self.amount_input.insert(0, amount)
        self.amount_input.pack(side=tk.RIGHT)

        # At some point I just do not understand how self works in python
        self.delete_button = tk.Button(self, text="×", command=lambda : self.delete_function(self.id))
        self.delete_button.bind("<Button-1>", lambda *args : self.event_generate("<<Document-Altered>>"))
        self.delete_button.pack(side=tk.RIGHT)
    
    @property
    def element(self):
        to_return = self.element_input.element
        if to_return in element_names:
            return to_return
        else:
            raise UserInputException("Please select an element from the dropdown for every input.")
        
    @property
    def amount(self):
        try:
            return float(self.amount_input.get())
        except ValueError:
            raise UserInputException("Please input a value for all element amounts.")

class ElementDictionaryInput(tk.Frame):
    """dictionary input mapping a dropdown of an element to a number. Supports multiple elements"""
    class ElementPairList(tk.Frame):
        def delete_pair(self, id: int):
            for (index, pair) in enumerate(self.pairs):
                if pair.id == id:
                    pair.destroy()
                    del self.pairs[index]
                    break
        
        def add_pair(self, element: str, amount: str):
            new_element = ElementDictionaryPair(self, delete_function=self.delete_pair, id=self.current_id, element=element, amount=amount)
            self.current_id += 1
            self.pairs.append(new_element)
            new_element.pack()

        def add_empty_pair(self):
            self.add_pair("", "")
        
        def __init__(self, parent) -> None:
            super(ElementDictionaryInput.ElementPairList, self).__init__(parent)

            self.pairs: "List[ElementDictionaryPair]" = [ElementDictionaryPair(self, delete_function=self.delete_pair, id=0)]

            for pair in self.pairs:
                pair.pack()
            
            self.current_id = len(self.pairs)
        
        def clear(self):
            for pair in self.pairs:
                pair.destroy()
            
            self.pairs = []

    def __init__(self, parent) -> None:
        super(ElementDictionaryInput, self).__init__(parent)

        self.pair_list = self.ElementPairList(self)
        self.pair_list.pack()

        self.add_button = tk.Button(self, text="Add Element", command=self.pair_list.add_empty_pair)
        self.add_button.pack()

    @property
    def elements(self) -> dict:
        ans = dict()
        for pair in self.pair_list.pairs:
            ans[get_element_by_name(pair.element)] = pair.amount
        
        return ans
    
    @elements.setter
    def elements(self, new_elements: dict) -> None:
        # Clear the old elements
        self.pair_list.clear()

        # Input the new elements
        for key, amount in new_elements.items():
            # Check if element is a symbol in the list of elements
            for element in elements:
                # Check if they only put the symbol in
                if key == element.symbol:
                    key = element.full_name
                    break
            
            self.pair_list.add_pair(key, amount)

class CompoundSelect(tk.Frame):
    """Selection class for a chemical compound. Implemented by fuel selection and by oxidizer selection."""

    def pack_custom(self):
        self.custom_frame = tk.Frame(self)
        self.custom_frame.pack()

        heat_frame = tk.Frame(self.custom_frame)
        heat_frame.pack()
        tk.Label(heat_frame, text="Heat of Formation: ").pack(side=tk.LEFT)
        self.formation_heat_input = InputMolarMassUnits(heat_frame, unit_conversions={
            "kJ/mol": 1,
            # Because we want to divide by the molar mass, we use a negative one for the power
            # Converting 1000 grams to one kilogram is multiplication by 1000
            "kJ/kg": MolarMassMultiplier(multiplier=1000, power=-1)
            }, precision=None, change_on_update=False, width=8)

        self.formation_heat_input.pack(side=tk.LEFT)

        self.composition_input = ElementDictionaryInput(self.custom_frame)
        self.composition_input.pack()
    
    def pack_preset(self):
        self.preset_frame = tk.Frame(self)
        self.preset_frame.pack()
        
        self.preset_selection = SearchableDropdown(self.preset_frame, self.preset_compound_options)
        self.preset_selection.pack()

    def toggle_custom(self):
        if self.is_custom:
            self.preset_frame.destroy()
            self.pack_custom()
        else:
            self.custom_frame.destroy()
            self.pack_preset()

    def __init__(self, parent, name: str="", preset_compound_options: "List[str]"=[], help_func=None):
        super(CompoundSelect, self).__init__(parent)

        self.preset_compound_options = preset_compound_options

        title_frame = tk.Frame(self)
        title_label = tk.Label(title_frame, text=name)
        title_label.configure(font=subtitle_font)
        title_frame.columnconfigure(0, weight=1)
        title_frame.columnconfigure(3, weight=1)
        title_label.grid(row=0, column=1)
        if help_func is not None:
            help_button(title_frame, help_func).grid(row=0, column=2, padx=(2, 0))

        title_frame.pack(pady=(15, 0), ipadx=50, expand=False, fill="none")
        
        self.custom_frame = tk.Frame(self)
        self.custom_frame.pack(pady=(0, 20))
        self.custom_label = tk.Label(self.custom_frame, text="Custom: ")
        self.custom_label.pack(side=tk.LEFT)
        self.isCustomVar = tk.BooleanVar(value=False)
        self.customCheck = tk.Checkbutton(self.custom_frame, text = "", variable = self.isCustomVar, \
                        onvalue=True, offvalue=False, command=self.toggle_custom, cursor="hand2")
        self.customCheck.pack(side=tk.RIGHT)

        if self.is_custom:
            self.pack_custom()
        else:
            self.pack_preset()

    def clear(self):
        # FIXME: I need to make this not a double toggle if I want to remember double toggles
        if not self.is_custom:
            # Perform the click effects
            self.isCustomVar.set(not self.isCustomVar.get())
            self.toggle_custom()
        
        self.isCustomVar.set(not self.isCustomVar.get())
        self.toggle_custom()

    @property
    def is_custom(self) -> bool:
        return self.isCustomVar.get()
    
    @is_custom.setter
    def is_custom(self, new_value: bool) -> None:
        if self.is_custom == new_value:
            return
        
        self.isCustomVar.set(not self.isCustomVar.get())
        self.toggle_custom()

    
    @property
    def formation_heat(self):
        if self.is_custom:
            try:
                return float(self.formation_heat_input.get_base_value(self.elements))
            except NonExistentElementException as e:
                print(e)
                raise UserInputException("Select an element from the listed options.")
            except ValueError as e:
                print(e)
                raise UserInputException("Input a number for heat of formation.")
        
        raise Exception("Attempting to access heat of formation from a preset.")
    
    @formation_heat.setter
    def formation_heat(self, new_value) -> None:
        try:
            float(new_value)

            self.formation_heat_input.value = new_value
        except ValueError as e:
            print(e)
            raise Exception("Cannot set formation heat to a non-float value")

    @property
    def elements(self):
        if self.is_custom:
            return self.composition_input.elements
        
        raise Exception("Attempting to access list of elements from a preset.")
    
    @elements.setter
    def elements(self, new_elements: dict) -> None:
        self.composition_input.elements = new_elements

    @property
    def name(self):
        if self.is_custom:
            raise Exception("Custom compounds do not have names. Check whether the selection is_custom.")
        
        to_return = self.preset_selection.value
        if to_return in self.preset_compound_options:
            return to_return
        
        raise UserInputException("Please select a preset from the given options.")
    
    @name.setter
    def name(self, new_value):
        self.preset_selection.value = new_value