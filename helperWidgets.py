from glob import glob
import tkinter as tk
from tkinter import ttk
from turtle import right

from images import images

class NumericalEntry(tk.Entry):
    def __init__(self, parent, *args, **kwargs):
        vcmd = (parent.register(self.validate),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        
        tk.Entry.__init__(self, parent, *args, validate = 'key', validatecommand=vcmd, **kwargs)
        self.parent = parent

    def validate(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
        if value_if_allowed == "":
            return True
        
        if value_if_allowed:
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return False


class LabeledInput(tk.Frame):
    def __init__(self, parent, label_text="Labeled input: ", uniform="", numerical=False, help_func=None):
        super(LabeledInput, self).__init__(parent)

        if uniform:
            self.columnconfigure(0, uniform=uniform, minsize=10)
            self.columnconfigure(1, weight=1, uniform=uniform)
        
        self.label = tk.Label(self, text=label_text)
        self.label.grid(row=0, column=0, sticky="e")

        entry_frame = tk.Frame(self)
        entry_frame.grid(row=0, column=1, sticky="w")

        if numerical:
            self.entry = NumericalEntry(entry_frame, width=8)
        else:
            self.entry = ttk.Entry(entry_frame, width=8)
        
        self.entry.pack(side=tk.LEFT)
        if help_func is not None:
            help_button(entry_frame, command=help_func).pack(side=tk.LEFT)
    
    def clear(self):
        self.entry.delete(0, tk.END)

    @property
    def value(self):
        return self.entry.get()
    
    @value.setter
    def value(self, new_value):
        self.entry.delete(0, tk.END) #deletes the current value
        self.entry.insert(0, new_value)



def help_button(parent, command):
    # return tk.Button(parent, image=images["help"], command=command, borderwidth=0, takefocus=0, cursor="hand2", width=12, height=12), background="#CCC"
    return tk.Button(parent, text="?", command=command, borderwidth=0, takefocus=0, cursor="hand2", font=("Arial", 8, "underline"))
    


class LabeledOutput(tk.Frame):
    def update_value(self, new_value: str):
        self.output.configure(text=new_value)

    def __init__(self, parent, prefix: str="Label: s", initial_value: str="", uniform="", help_func=None):
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1, uniform=uniform)
        self.grid_columnconfigure(1, weight=1, uniform=uniform)

        self.prefix_label = tk.Label(self, text=prefix)
        self.prefix_label.grid(row=0, column=0, sticky="e")

        right_frame = tk.Frame(self)
        right_frame.grid(row=0, column=1, sticky="w")
        self.output = tk.Label(right_frame, text=initial_value)
        self.output.pack(side=tk.LEFT)

        if help_func is not None:
            help_button(right_frame, help_func).pack(side=tk.LEFT)


    def clear(self):
        self.update_value("")