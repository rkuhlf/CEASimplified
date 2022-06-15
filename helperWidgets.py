import tkinter as tk
from tkinter import ttk
from typing import Dict

from toPrecision import std_notation

from images import images


# Probably should have made some kind of Unit class from which everything inherits and has get_converted and get_unconverted
class MultiplyAndAdd:
    def __init__(self, multiplier=1, add=0) -> None:
        self.multiplier = multiplier
        self.add = add
    
    def get_converted(self, value: float) -> float:
        return value * self.multiplier + self.add
        
    
    def get_unconverted(self, value: float) -> float:
        return (value - self.add) / self.multiplier


def validate_to_float(text: str, empty=True):
    """Empty is what to return if it is empty"""
    if text == "":
        return empty
    
    if text:
        try:
            float(text)
            return True
        except ValueError:
            return False
    else:
        return False

def help_button(parent, command):
    # return tk.Button(parent, image=images["help"], command=command, borderwidth=0, takefocus=0, cursor="hand2", width=12, height=12), background="#CCC"
    return tk.Button(parent, text="?", command=command, borderwidth=0, takefocus=0, cursor="hand2", font=("Arial", 8, "underline"))
    

class NumericalEntry(tk.Entry):
    def __init__(self, parent, precision=None, *args, **kwargs):
        vcmd = (parent.register(self.validate),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        
        self.precision = precision
        if "textvariable" not in kwargs.keys():
            self.text_variable = tk.StringVar()
            kwargs["textvariable"] = self.text_variable
        kwargs["textvariable"].trace("w", lambda a, b, c : self.event_generate("<<Document-Altered>>"))
        
        tk.Entry.__init__(self, parent, *args, validate = 'key', validatecommand=vcmd, **kwargs)
        self.parent = parent

    def validate(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
        return validate_to_float(value_if_allowed)
    
    def insert(self, index: int, string: str) -> None:
        if validate_to_float(string, empty=False):
            if self.precision != None:
                string = std_notation(float(string), self.precision)
        
        
        return super().insert(index, string)

    @property
    def value(self) -> str:
        return self.text_variable.get()
    
    @value.setter
    def value(self, v: str):
        self.text_variable.set(v)


class UnitsDropDown(tk.Frame):
    def __init__(self, parent, unit_conversions: Dict[str, float]={}, handle_units_change=lambda : ..., **kwargs):
        super().__init__(parent, **kwargs)
        self.handle_units_change = handle_units_change
        self.unit_conversions = unit_conversions

        self.units_variable = tk.StringVar(parent)
        self.units_variable.set(list(unit_conversions.keys())[0])
        self.units_input = ttk.OptionMenu(self, self.units_variable, self.units_variable.get(), *list(unit_conversions.keys()), command=self.handle_units_change_wrapper)
        self.units_input.pack(side=tk.LEFT)

        self.previous_units = self.units
    
    @property
    def units(self):
        return self.units_variable.get()
    
    @units.setter
    def units(self, new_units):
        self.units_variable.set(new_units)
        self.handle_units_change_wrapper()
    
    def handle_units_change_wrapper(self, _event=...):
        self.handle_units_change(self.previous_units, self.units)

        self.previous_units = self.units
    
    def get_conversion(self, old_units, value) -> float:
        """Returns the conversion factor to match the drop down"""
        old_conversion = self.unit_conversions.get(old_units)

        if isinstance(old_conversion, MultiplyAndAdd):
            base = old_conversion.get_unconverted(value)
        else:
            base = value / old_conversion
        
        new_conversion = self.unit_conversions.get(self.units)
        if isinstance(new_conversion, MultiplyAndAdd):
            return new_conversion.get_converted(base)
        else:
            return base * new_conversion
        

class NumericalEntryWithUnits(tk.Frame):
    def __init__(self, parent, unit_conversions: Dict[str, float]={}, precision=2, change_on_update=True, on_units_update=lambda *args :..., **kwargs) -> None:
        """Additional keyword arguments are passed to the entry. If no units are passed, it will create an empty dropdown"""
        self.precision = precision
        super().__init__(parent, **kwargs)

        self.on_units_update = on_units_update
        self.change_on_update = change_on_update
        self.unit_conversions = unit_conversions
        
        self.text_variable = tk.StringVar()
        self.entry = NumericalEntry(self, precision=precision, textvariable=self.text_variable, **kwargs)
        self.entry.pack(side=tk.LEFT)

        self.units_dropdown = UnitsDropDown(self, unit_conversions, handle_units_change=self.handle_units_change)
        self.units_dropdown.pack(side=tk.LEFT)
    
    @property
    def value(self) -> str:
        return self.entry.get()
    
    @value.setter
    def value(self, v: str):
        # The text variable technique works even if it is set as read-only
        if self.precision is not None:
            if v != "":
                v = std_notation(float(v), self.precision)
        
        self.text_variable.set(v)

        self.event_generate("<<Document-Altered>>")
        
    @property
    def base_value(self) -> float:
        return float(self.value) / self.unit_conversions.get(self.units)
    
    @property
    def units(self):
        return self.units_dropdown.units
    
    @units.setter
    def units(self, new_units):
        self.units_dropdown.units = new_units


    def handle_units_change(self, old_units, new_units):
        self.on_units_update(old_units, new_units)

        if self.value.strip() == "":
            return
        
        if self.change_on_update:
            self.value = float(self.value) / self.unit_conversions.get(old_units) * self.unit_conversions.get(new_units)

        
        # No need to update the saved state, since units are only a visual thing; they are all stored in CEA units


class LabeledInput(tk.Frame):
    def create_input(self, parent):
        if self.numerical:
            entry = NumericalEntry(parent, width=8)
        else:
            entry = ttk.Entry(parent, width=8)
        
        entry.pack(side=tk.LEFT)

        return entry
        
    def __init__(self, parent, label_text="Labeled input: ", uniform="", numerical=False, help_func=None):
        super(LabeledInput, self).__init__(parent)
        self.numerical = numerical

        if uniform:
            self.columnconfigure(0, uniform=uniform, minsize=10)
            self.columnconfigure(1, weight=1, uniform=uniform)
        
        self.label = tk.Label(self, text=label_text)
        self.label.grid(row=0, column=0, sticky="e")

        entry_frame = tk.Frame(self)
        entry_frame.grid(row=0, column=1, sticky="w")

        self.entry = self.create_input(entry_frame)
        
        if help_func is not None:
            help_button(entry_frame, command=help_func).pack(side=tk.LEFT)
    
    def clear(self):
        self.entry.delete(0, tk.END)

    @property
    def value(self):
        return self.entry.get()
    
    @value.setter
    def value(self, new_value):
        self.event_generate("<<Document-Altered>>")
        self.entry.delete(0, tk.END)
        self.entry.insert(0, new_value)


class LabeledOutput(tk.Frame):
    def update_value(self, new_value: str) -> None:
        self.output.configure(state="normal")
        self.output.delete(0, tk.END)
        self.output.insert(0, new_value)
        self.output.configure(state="readonly")
    
    def create_output(self, parent) -> tk.Entry:
        if self.numerical:
            entry = NumericalEntry(parent, self.precision)
        else:
            entry = tk.Entry(parent)
        
        entry.insert(0, self.initial_value)
        entry.configure(state="readonly")

        return entry

    def __init__(self, parent, prefix: str="Label: s", initial_value: str="", uniform="", help_func=None, numerical=False, precision=2):
        super().__init__(parent)
        self.numerical = numerical
        self.precision = precision
        self.initial_value = initial_value

        self.grid_columnconfigure(0, weight=1, uniform=uniform)
        self.grid_columnconfigure(1, weight=1, uniform=uniform)

        self.prefix_label = tk.Label(self, text=prefix)
        self.prefix_label.grid(row=0, column=0, sticky="e")

        right_frame = tk.Frame(self)
        right_frame.grid(row=0, column=1, sticky="w")
        self.output = self.create_output(right_frame)
        self.output.pack(side=tk.LEFT)

        if help_func is not None:
            help_button(right_frame, help_func).pack(side=tk.LEFT, padx=(5, 0))


    def clear(self):
        self.update_value("")



class LabeledOutputWithUnits(LabeledOutput):
    # This class is a little confusing because output is a numerical entry with units and entry is a numerical entry
    def create_output(self, parent) -> NumericalEntryWithUnits:
        entry_frame = NumericalEntryWithUnits(parent, self.unit_conversions, precision=self.precision)
        entry_frame.value = self.initial_value
        entry_frame.entry.configure(state="readonly")

        return entry_frame
    
    def update_value(self, new_value: str, units: str="") -> None:
        """Takes a value and the units that it is in. Will be converted to the units that the label is in."""
        # Required because this is how the clear functionality does it
        if units == "" and new_value == "":
            self.entry.configure(state="normal")
            self.output.value = new_value
            self.entry.configure(state="readonly")
            return


        if validate_to_float(new_value, empty=False):
            new_value = float(new_value)
            new_value /= self.unit_conversions[units]
            new_value *= self.unit_conversions[self.output.units]
            new_value = str(new_value)
        
        self.entry.configure(state="normal")
        self.output.value = new_value
        self.entry.configure(state="readonly")
    
    def __init__(self, parent, prefix: str="Label: s", initial_value: str="", unit_conversions: dict={}, uniform="", help_func=None, precision=2, **kwargs):
        self.precision = precision
        self.unit_conversions = unit_conversions
        super().__init__(parent, prefix, initial_value, uniform, help_func, precision=precision, numerical=True, **kwargs)

    @property
    def entry(self) -> NumericalEntryWithUnits:
        return self.output.entry
            

class LabeledInputWithUnits(LabeledInput):
    def create_input(self, parent) -> NumericalEntry:
        self.entry_with_units = NumericalEntryWithUnits(parent, self.unit_conversions, precision=None, width=8, change_on_update=True)
        self.entry_with_units.pack(side=tk.LEFT)

        return self.entry_with_units.entry
    
    def __init__(self, parent, label_text="Labeled input: ", unit_conversions=[], uniform="", help_func=None, **kwargs):
        self.unit_conversions = unit_conversions
        super().__init__(parent, label_text, uniform, numerical=True, help_func=help_func, **kwargs)


    @property
    def base_value(self):
        return self.entry_with_units.base_value