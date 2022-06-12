


import tkinter as tk
from tkinter import ttk
from typing import List
from elements import element_names


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

        self.text_variable = tk.StringVar()
        self.text_variable.trace("w", lambda a, b, c : self.event_generate("<<Document-Altered>>"))
        self.combo_box = ttk.Combobox(self, textvariable=self.text_variable)
        self.combo_box['values'] = items
        self.combo_box.bind('<KeyRelease>', self.check_input)
        self.combo_box.pack()
    
    @property
    def value(self):
        return self.combo_box.get()
    
    @value.setter
    def value(self, v) -> None:
        self.combo_box.set(v)


class ElementDropDown(tk.Frame):
    def __init__(self, parent):
        super(ElementDropDown, self).__init__(parent)

        self.elementDropDown = SearchableDropdown(self, element_names)
        self.elementDropDown.pack()

    @property
    def element(self) -> str:
        current: str = self.elementDropDown.value
        
        if current in element_names:
            return current

        return ""
    
    @element.setter
    def element(self, new_element) -> None:
        self.elementDropDown.value = new_element

        self.event_generate("<<Document-Altered>>")
