import tkinter as tk
from tkinter import ttk
from toPrecision import std_notation

from images import images

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
        tk.Entry.__init__(self, parent, *args, validate = 'key', validatecommand=vcmd, **kwargs)
        self.parent = parent

    def validate(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
        return validate_to_float(value_if_allowed)
    
    def insert(self, index: int, string: str) -> None:
        if validate_to_float(string, empty=False):
            # TODO: make the precision more optional so that inputs cannot have 10 digits of accuracy
            if self.precision != None:
                string = std_notation(float(string), self.precision)

        return super().insert(index, string)

class NumericalEntryWithUnits(tk.Frame):
    def __init__(self, parent, unit_conversions: dict={}, precision=2, change_on_update=True, **kwargs) -> None:
        """Additional keyword arguments are passed to the entry. If no units are passed, it will create an empty dropdown"""
        self.precision = precision
        super().__init__(parent, **kwargs)

        self.change_on_update = change_on_update
        self.unit_conversions = unit_conversions
        
        self.text_variable = tk.StringVar()
        self.entry = NumericalEntry(self, precision=precision, textvariable=self.text_variable, **kwargs)
        self.entry.pack(side=tk.LEFT)

        self.units_variable = tk.StringVar(parent)
        self.units_variable.set(list(unit_conversions.keys())[0])
        self.units_input = ttk.OptionMenu(self, self.units_variable, self.units_variable.get(), *list(unit_conversions.keys()), command=self.handle_unit_change)
        self.units_input.pack(side=tk.LEFT)

        self.previous_units = self.units
    
    @property
    def value(self) -> str:
        return self.entry.get()
    
    @value.setter
    def value(self, v: str):
        # Not working for some reason; is no longer disabled while setting
        if v != "":
            v = std_notation(float(v), self.precision)
        self.text_variable.set(v)
        
    @property
    def base_value(self):
        return self.value / self.unit_conversions.get(self.units)
    
    @property
    def units(self):
        return self.units_variable.get()
    
    def handle_unit_change(self, new_units):
        if self.change_on_update:
            self.value = float(self.value) / self.unit_conversions.get(self.previous_units) * self.unit_conversions.get(new_units)

            self.previous_units = self.units


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
    
    def update_value(self, new_value: str, units: str) -> None:
        """Takes a value and the units that it is in. Will be converted to the units that the label is in."""
        
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
    def create_input(self, parent) -> NumericalEntryWithUnits:
        entry_frame = NumericalEntryWithUnits(parent, self.unit_conversions, precision=None, width=8, change_on_update=False)
        entry_frame.pack(side=tk.LEFT)

        return entry_frame.entry
    
    def __init__(self, parent, label_text="Labeled input: ", unit_conversions=[], uniform="", help_func=None, **kwargs):
        self.unit_conversions = unit_conversions
        super().__init__(parent, label_text, uniform, numerical=True, help_func=help_func, **kwargs)


