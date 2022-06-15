
# There are no default units for heat of formation because frick that
# TODO: figure out why increasing the area ratio always gives a better Isp


import os
import pickle
import re
import subprocess

import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk
from tkinter import messagebox
import traceback

from HelpWindow import AREA_RATIO_WINDOW, CEA_WINDOW, CF_WINDOW, CSTAR_WINDOW, FUEL_WINDOW, ISP_WINDOW, OF_WINDOW, OXIDIZER_WINDOW, PRESSURE_WINDOW
from PropellantSelect import CompoundSelect
import os.path

from fonts import title_font, subtitle_font

from typing import List

from Exceptions import PresetException, UnknownCEAException, UserInputException

from compound import CustomCompound, PresetCompound
from helperWidgets import LabeledInput, LabeledInputWithUnits, LabeledOutput, LabeledOutputWithUnits, MultiplyAndAdd, UnitsDropDown, help_button
import images
from toPrecision import list_to_precision

DATA_FOLDER = "./CEAData"
FCEA_FOLDER = "./FCEA"
CREATE_NO_WINDOW = 0x08000000
APPLICATION_NAME = "CEA Simplified"

PRESSURE_UNITS = {
    "psia": 1,
    "Pa": 6894.75729,
    "atm": 0.068046,
    "bar": 0.0689476094997927,
    "torr": 51.714960008010713466
}
VELOCITY_UNITS = {
    "m/s": 1,
    "ft/s": 3.28084,
    "mph": 2.23694,
    "kph": 3.6
}
ISP_UNITS = {
    "s": 1,
    "m/s": 9.81,
    "ft/s": 32.2
}

TEMPERATURE_UNITS = {
    "K": MultiplyAndAdd(),
    "C": MultiplyAndAdd(add=-273.15),
    "F": MultiplyAndAdd(multiplier=9/5, add=-559.67)
}

DENSITY_UNITS = {
    "kg/m^3": 1,
    "g/ml": 0.001,
    "lb/in^3": 3.61273e-5,
    "lb/ft^3": 0.062428,
    "slugs/ft^3": 0.00194032033
}


def generate_name(file: str=None, saved=True):
    if file is None:
        return f"{APPLICATION_NAME} - Unsaved*"
    
    name = f"{APPLICATION_NAME} - {file}"
    if not saved:
        name += "*"
    
    return name

def hide_file(path: str):
    subprocess.run(f"attrib +h {path}", creationflags=CREATE_NO_WINDOW)

def unhide_file(path: str):
    subprocess.run(f"attrib -h {path}", creationflags=CREATE_NO_WINDOW)


def string_to_dict(string: str):
    """Transform a string like C 1 H 2 into {C: 1, H: 2}"""
    string = string.strip()
    items = string.split()
    ans = dict()

    if len(items) % 2 != 0:
        raise ValueError(f"This string ({string}) cannot be converted into a dictionary because it has an odd number of values.")

    for i in range(len(items) // 2):
        ans[items[i * 2]] = items[i * 2 + 1]
    
    return ans


class Inputs(tk.Frame):
    """Input set for very basic CEA"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        top_spacer = tk.Frame(self).pack(expand=True, fill=tk.BOTH)

        help_wrapper = tk.Frame(self)
        help_wrapper.pack(pady=(0, 40))
        tk.Label(help_wrapper, text="CEA Simplified", font=title_font).pack(side=tk.LEFT)
        help_button(help_wrapper, command=CEA_WINDOW).pack(padx=(5, 0), side=tk.RIGHT)

        text_inputs = tk.Frame(self)
        text_inputs.pack(pady=20)

        # TODO: Add an optimize button next to it. Also requires decoupling the simulation code. And making it a grid layout
        # Use 🗲 as icon
        self.OF_input = LabeledInput(text_inputs, "O/F: ", numerical=True, uniform="main", help_func=OF_WINDOW)
        self.OF_input.pack()

        self.pressure_input = LabeledInputWithUnits(text_inputs, "Pressure: ", unit_conversions=PRESSURE_UNITS, uniform="main", help_func=PRESSURE_WINDOW)
        self.pressure_input.pack()

        self.area_ratio_input = LabeledInput(text_inputs, "Area Ratio: ", numerical=True, uniform="main", help_func=AREA_RATIO_WINDOW)
        self.area_ratio_input.pack()

        sep = ttk.Separator(self, orient=tk.HORIZONTAL)
        sep.pack(fill="x")
        
        self.propellants_frame = tk.Frame(self)
        self.propellants_frame.pack(fill=tk.BOTH, expand=True)
        self.propellants_frame.grid_rowconfigure(0, weight=1)
        self.propellants_frame.grid_columnconfigure(0, weight=1, uniform="propellant_column")
        self.propellants_frame.grid_columnconfigure(2, weight=1, uniform="propellant_column")

        padding: float = 20

        self.fuel_select = CompoundSelect(self.propellants_frame, name="Select Fuel", preset_compound_options=["CH4", "H2", "RP-1"], help_func=FUEL_WINDOW)
        self.fuel_select.grid(row=0, column=0, padx=padding, sticky="ne")

        sep = ttk.Separator(self.propellants_frame, orient=tk.VERTICAL)
        sep.grid(row=0, column=1, sticky="nsew")

        self.oxidizer_select = CompoundSelect(self.propellants_frame, name="Select Oxidizer", preset_compound_options=["Air", "H2O2(L)", "N2O", "O2", "CL2", "F2", "N2H4(L)"], help_func=OXIDIZER_WINDOW)
        self.oxidizer_select.grid(row=0, column=2, padx=padding, sticky="nw")

    def apply_units(self, selected_units):
        self.pressure_input.entry_with_units.units = selected_units["pressure input"]

    def get_units(self) -> dict:
        return {
            "pressure input": self.pressure_input.entry_with_units.units
        }

    def clear(self):
        self.OF_input.clear()
        self.pressure_input.clear()
        self.area_ratio_input.clear()

        self.fuel_select.clear()
        self.oxidizer_select.clear()

    @property
    def OF(self):
        try:
            return float(self.OF_input.value)
        except ValueError as e:
            print(e)
            raise UserInputException("Please input a value for the O/F ratio.")
    
    @property
    def pressure(self):
        try:
            return float(self.pressure_input.base_value)
        except ValueError as e:
            print(e)
            raise UserInputException("Please input a value for the chamber pressure.")
    
    @property
    def area_ratio(self):
        try:
            return float(self.area_ratio_input.value)
        except ValueError as e:
            print(e)
            raise UserInputException("Please input a value for the area ratio.")

    @property
    def fuel(self):
        "Constructs a fuel object and returns it"
        
        if self.is_custom_fuel:
            # Name of the compound does not matter to CEA unless it is a preset
            return CustomCompound("customFuel", self.fuel_select.formation_heat, self.fuel_select.elements)
        
        return PresetCompound(self.fuel_select.name)
    
    @property
    def oxidizer(self):
        "Constructs an oxidizer object and returns it"
        
        if self.is_custom_oxidizer:
            # Name of the compound does not matter to CEA unless it is a preset
            return CustomCompound("customOxidizer", self.oxidizer_select.formation_heat, self.oxidizer_select.elements)
        
        return PresetCompound(self.oxidizer_select.name)
    
    @property
    def is_custom_oxidizer(self):
        return self.oxidizer_select.is_custom
    
    @property
    def is_custom_fuel(self):
        return self.fuel_select.is_custom


class Outputs(tk.Frame):
    def pack_row(self, values: "List[str]"=[], start_col=0, row=0):
        for column, val in enumerate(values, start=start_col):
            self.entries[row][column].configure(text=val)

    def repack_conditions(self):
        """Update the content of the numerical outputs in a grid"""       
        
        precisions = [4, 3, 3, 3, 4]
        for index, row_data in enumerate(self.conditions_data):
            row_data = list_to_precision(row_data, precisions[index])
            self.pack_row(row_data, row=index)

    def update_display(self, new_outputs):
        self.cstar_display.update_value(new_outputs["cstar"], new_outputs["cstar units"])
        self.CF_display.update_value(new_outputs["CF"])
        self.Isp_display.update_value(new_outputs["Isp"], new_outputs["isp units"])

        velocities = []
        for sonic, mach in zip(new_outputs["sonicVelocity"], new_outputs["mach"]):
            new_velocity = float(sonic) * float(mach)
            velocities.append(new_velocity)
        
        pressures = new_outputs["pressure"]
        temperature = new_outputs["temperature"]
        density = new_outputs["density"]
        mach = new_outputs["mach"]

        for index, (data, input_units, display_units) in enumerate([
                (pressures, new_outputs["pressure units"], self.pressure_units),
                (temperature, new_outputs["temperature units"], self.temperature_units),
                (density, new_outputs["density units"], self.density_units),
                (mach, "", None),
                (velocities, new_outputs["velocity units"], self.velocity_units)
            ]):
            if input_units != "":
                data = list(map(lambda x : display_units.get_conversion(input_units, x), data))
                
            self.conditions_data[index] = data

        self.repack_conditions()

    def __init__(self, parent):
        super().__init__(parent)

        subtitle_offset = 0
        self.performance_label = tk.Label(self, text="Propulsion Characteristics")
        self.performance_label.configure(font=subtitle_font)
        self.performance_label.pack(pady=(0, subtitle_offset))
        performance = tk.Frame(self)
        performance.pack()

        self.cstar_display = LabeledOutputWithUnits(performance, prefix="Characteristic Velocity: ", help_func=CSTAR_WINDOW, uniform="outputs", unit_conversions=VELOCITY_UNITS, precision=4)
        self.cstar_display.pack()
        self.CF_display = LabeledOutput(performance, prefix="Nozzle Coefficient: ", help_func=CF_WINDOW, uniform="outputs", precision=3, numerical=True)
        self.CF_display.pack()

        self.Isp_display = LabeledOutputWithUnits(performance, prefix="Specific Impulse: ", help_func=ISP_WINDOW, uniform="outputs", unit_conversions=ISP_UNITS, precision=3)
        self.Isp_display.pack()


        self.conditions_label = tk.Label(self, text="Propulsion Conditions")
        self.conditions_label.configure(font=subtitle_font)
        self.conditions_label.pack(pady=(20, subtitle_offset))

        self.conditions = tk.Frame(self)
        self.conditions.pack()

        # Refactor to have a separate array of all of the numbers, then display it in the numerical entries
        row_title_offset = 5
        tk.Label(self.conditions, text=" Chamber ").grid(column=1, row=0, sticky="e", pady=(0, 5), padx=3)
        tk.Label(self.conditions, text=" Throat ").grid(column=2, row=0, sticky="e", pady=(0, 5), padx=3)
        tk.Label(self.conditions, text=" Exit ").grid(column=3, row=0, sticky="e", pady=(0, 5), padx=3)
        tk.Label(self.conditions, text="Pressure").grid(column=0, row=1, sticky="w", padx=row_title_offset)
        tk.Label(self.conditions, text="Temperature").grid(column=0, row=2, sticky="w", padx=row_title_offset)
        tk.Label(self.conditions, text="Density").grid(column=0, row=3, sticky="w", padx=row_title_offset)
        tk.Label(self.conditions, text="Mach Number").grid(column=0, row=4, sticky="w", padx=row_title_offset)
        tk.Label(self.conditions, text="Velocity").grid(column=0, row=5, sticky="w", padx=row_title_offset)

        # five rows of three blanks
        self.conditions_data = [[""] * 3] * 5
        self.entries = []
        for row_index in range(1, len(self.conditions_data) + 1):
            self.entries.append([])
            for column_index in range(1, len(self.conditions_data[0]) + 1):
                entry = tk.Label(self.conditions) #, text=f"{row_index}: {column_index}")
                entry.grid(row=row_index, column=column_index, sticky="e", padx=5)

                self.entries[row_index - 1].append(entry)

        def update_row_by_factor(row, factor, start_at=1):
            # No need to update anything if there is no data
            if "" in self.conditions_data[row]:
                return
            
            self.conditions_data[row] = list(map(lambda x : str(float(x) * factor), self.conditions_data[row]))
            self.repack_conditions()
        
        def update_row_for_temperature(row, prev_units: str, new_units: str):
            # Hard-coding this because the unit conversions are already monstrous and this should be the last time
            if "" in self.conditions_data[row]:
                return
            
            unconversion = TEMPERATURE_UNITS[prev_units].get_unconverted
            conversion = TEMPERATURE_UNITS[new_units].get_converted
        
            for index, value in enumerate(self.conditions_data[row]):
                base = unconversion(value)

                self.conditions_data[row][index] = conversion(base)

            self.repack_conditions()


        self.pressure_units = UnitsDropDown(self.conditions, PRESSURE_UNITS, lambda prev_units, new_units: update_row_by_factor(row=0, factor=PRESSURE_UNITS[new_units]/PRESSURE_UNITS[prev_units]))
        self.pressure_units.grid(row=1, column=4, sticky="w")

        self.temperature_units = UnitsDropDown(self.conditions, TEMPERATURE_UNITS, lambda prev_units, new_units: update_row_for_temperature(1, prev_units, new_units))
        self.temperature_units.grid(row=2, column=4, sticky="w")

        self.density_units = UnitsDropDown(self.conditions, DENSITY_UNITS, lambda prev_units, new_units: update_row_by_factor(row=2, factor=DENSITY_UNITS[new_units]/DENSITY_UNITS[prev_units]))
        self.density_units.grid(row=3, column=4, sticky="w")

        self.velocity_units = UnitsDropDown(self.conditions, VELOCITY_UNITS, lambda prev_units, new_units: update_row_by_factor(row=4, factor=VELOCITY_UNITS[new_units]/VELOCITY_UNITS[prev_units]))
        self.velocity_units.grid(row=5, column=4, sticky="w")

    def clear_conditions(self):
        self.conditions_data = [[""] * 3] * 5
        self.repack_conditions()

    def clear(self):
        self.Isp_display.clear()
        self.CF_display.clear()
        self.cstar_display.clear()

        self.clear_conditions()

    def apply_units(self, selected_units):
        self.cstar_display.output.units = selected_units["cstar output"]
        self.Isp_display.output.units = selected_units["isp output"]
        self.pressure_units.units = selected_units["pressure output"]
        self.temperature_units.units = selected_units["temperature output"]
        self.density_units.units = selected_units["density output"]
        self.velocity_units.units = selected_units["velocity output"]
    
    def get_units(self) -> dict:
        return {
            "cstar output": self.cstar_display.output.units,
            "isp output": self.Isp_display.output.units,
            "pressure output": self.pressure_units.units,
            "temperature output": self.temperature_units.units,
            "density output": self.density_units.units,
            "velocity output": self.velocity_units.units
        }
        


filetypes = (
    ('CEA files', '*.inp'),
    ('All files', '*.*')
)


class Editor(tk.Frame):
    def update_title(self, saved=True):
        if self.current_file == self.default_temp_file:
            root.title(generate_name())
        else:
            root.title(generate_name(self.current_file, saved))
        
    def set_unsaved(self):
        self.update_title(False)
        self.unsaved = True
    
    def set_saved(self):
        self.update_title()
        self.unsaved = False
    
    def check_saved(self):
        if self.unsaved:
            should_continue = messagebox.askokcancel("Erase Data?", "This will erase unsaved progress. Are you sure you want to continue?")
        
            return should_continue
        
        return True

    def clear(self):
        self.inputs.clear()
        self.outputs.clear()

    def new_file(self):
        if not self.check_saved():
            return
        
        # set to temp and clear inputs
        self.set_current_file(self.default_temp_file)
        self.clear()

        self.set_unsaved()

    def prompt_and_load_file(self):
        if not self.check_saved():
            return
        
        filename = fd.askopenfilename(
            title='Open an Input File',
            initialdir=f'./{DATA_FOLDER}',
            filetypes=filetypes)
        
        if not filename:
            return
        
        self.load_file(filename)

    def load_file(self, file: str):
        """Requires file end in .inp"""
        if not file.endswith(".inp"):
            raise UserInputException("All files must end with .inp")
        
        self.set_current_file(file[:-4])
        print(f"Attempting to load {self.current_file}")

        # Create the file if it does not exist, append so that nothing is erased
        # TODO: make it hidden
        open(self.current_file_input, "a+")
        
        if self.current_file == self.default_temp_file:
            # Make it hidden every time because it is probably not expensive
            hide_file(self.current_file_input)
        
        with open(self.current_file_input, "r") as f:
            text = f.read()

            def possible_load(prefix: str, input: LabeledInput):
                value = re.search(f"{prefix}=(\d+\.\d+)", text)
                
                if value:
                    input.value = value.groups()[0]
                else:
                    input.clear()
            
            possible_load("o/f", self.inputs.OF_input)
            possible_load("p,psia", self.inputs.pressure_input)
            possible_load("sup,ae/at", self.inputs.area_ratio_input)

            def update_propellant_select(prefix: str, select_object: CompoundSelect):
                # note that . does not include new lines and h checks to see if it starts the enthalpy on the next line
                custom_input = re.search(f"{prefix}=.*\s*h,kj/mol=(\d+\.\d+)(.*)", text)
                if custom_input:
                    select_object.is_custom = True

                    enthalpy = custom_input.groups()[0]
                    select_object.formation_heat = enthalpy

                    element_string = custom_input.groups()[1]
                    element_dictionary = string_to_dict(element_string)
                    select_object.elements = element_dictionary
                else:
                    preset_selection = re.search(f"{prefix}=(.*?)\s", text)

                    if preset_selection:
                        select_object.is_custom = False
                        select_object.name = preset_selection.groups()[0]
                    else:
                        # It is not custom or preset (we found nothing)
                        select_object.clear()
            
            update_propellant_select("fuel", self.inputs.fuel_select)
            update_propellant_select("oxid", self.inputs.oxidizer_select)
        
        self.set_saved()
    
    def save_as_current_file(self):
        name = fd.asksaveasfilename(
                title='Save as',
                initialdir=f'./{DATA_FOLDER}',
                filetypes=filetypes)
        
        if not name:
            return
            
        self.set_current_file(name, has_been_saved=False)

        self.save_file()

    def save_current_file(self):
        if self.current_file == self.default_temp_file:
            self.save_as_current_file()
        else:
            self.save_file()
    
    def save_file(self):
        # TODO: make a save function that does not require everything to be filled out
        successful = self.generate_file()

        if successful:
            self.set_saved()

    def generate_file(self):
        "Creates and writes data to the proper input file. Displays errors on GUI."
        try:
            # You cannot open a hidden file with w+            
            if os.path.isfile(self.current_file_input):
                unhide_file(self.current_file_input)

            # Opens and creates if it does not currently exist
            with open(self.current_file_input, "w+") as f:
                f.write(f"problem   case={self.current_file} o/f={self.inputs.OF},\n")
                # k actually does nothing
                f.write("    rocket  tcest,k=3800\n")
                f.write(f"p,psia={self.inputs.pressure},\n")
                
                f.write(f"sup,ae/at={self.inputs.area_ratio}\n")
                f.write("react\n")

                # Assume room temperature because it really does not matter
                selected_fuel = self.inputs.fuel
                f.write(f"fuel={selected_fuel.name} wt=1  t,f=70\n")
                if self.inputs.is_custom_fuel:
                    f.write(f"    h,kj/mol={selected_fuel.formation_heat}  {selected_fuel.elements_string()}\n")
                
                selected_oxidizer = self.inputs.oxidizer
                f.write(f"oxid={selected_oxidizer.name} wt=1  t,f=70\n")
                if self.inputs.is_custom_oxidizer:
                    f.write(f"    h,kj/mol={selected_oxidizer.formation_heat}  {selected_oxidizer.elements_string()}\n")
                
                f.write("end\n")
            if self.current_file == self.default_temp_file:
                # Make it hidden every time because it is probably not expensive
                hide_file(self.current_file_input)

        except PresetException:
            messagebox.showerror(title="No Presets", message="Unfortunately, preset propellants are not yet fully implemented")
        except UserInputException as e:
            messagebox.showerror(title="Improper Input", message=e.args[0])
        except PermissionError as e:
            print(e)
            messagebox.showerror(title="Permission Error", message=f"Could not load file {self.current_file_input} due to insufficient permissions.")
        else:
            # Returns true if there are no exceptions
            self.set_saved()
            return True
        
        return False

    def read_output_file(self) -> dict:
        try:
            outputs = dict()
            with open(self.current_file_output, "r") as f:
                text = f.read()

                cstar = re.search("CSTAR, M\/SEC\s*(\d*(\.\d*)?)", text)
                cf = re.search("CF.*?(\d+(.\d*)?)\n", text)
                metric_Isp = re.search("Isp, M/SEC.*?(\d+(.\d*)?)\n", text)
                if cstar is None or cf is None or metric_Isp is None:
                    # For some reason the CEA file did not generate as expected
                    raise UnknownCEAException()
                
                outputs["cstar units"] = "m/s"
                outputs["cstar"] = cstar.groups()[0]
                outputs["CF"] = cf.groups()[0]
                metric_Isp = metric_Isp.groups()[0]
                metric_Isp = float(metric_Isp)
                metric_Isp /= 9.81
                # Divide by the acceleration of gravity to get it in seconds
                outputs["Isp"] = str(metric_Isp)
                outputs["isp units"] = "s"

                def process_column(prefix, to_assign, conversion_func=lambda x : x):
                    values = re.search(f"{prefix}.*?(\d.*)\n", text).groups()[0]
                    values = values.split()
                    def float_from_CEA(value: str):
                        try:
                            return float(value)
                        except ValueError:
                            try:
                                # exclude any leading negatives, then add the one back in for the index
                                split = value[1:].index("-") + 1
                            except ValueError:
                                split = value[1:].index("+") + 1

                            power = int(value[split:])
                            return float(value[:split]) * 10 ** power


                    values = list(map(float_from_CEA, values))

                    # I have no clue why, but occasionally CEA gives output like "RHO, KG/CU M    1.0632 0 6.6109-1 7.8850-2". Hopefully this should fix most of it
                    i = 0
                    while len(values) > 3 and i < len(values):
                        if values[i] == 0:
                            del values[i]
                        else:
                            i += 1

                    values = list(map(conversion_func, values))
                    outputs[to_assign] = values
                
                outputs["pressure units"] = "bar"
                outputs["temperature units"] = "K"
                outputs["density units"] = "kg/m^3"
                outputs["velocity units"] = "m/s"
                process_column("P, BAR", "pressure", lambda pressure: pressure)
                process_column("T, K", "temperature", lambda temperature: temperature)
                process_column("RHO, KG/CU M", "density")
                process_column("MACH NUMBER", "mach")
                process_column("SON VEL,M/SEC", "sonicVelocity")
            
            if self.current_file == self.default_temp_file:
                hide_file(self.current_file_output)

            return outputs
        except UnknownCEAException:
            result = messagebox.askquestion("Unknown CEA Exception", "There was an error in the CEA program that could not be identified. Open raw output for debugging?", icon="error")

            if result == "yes":
                subprocess.run(f"notepad {self.current_file_output}", creationflags=CREATE_NO_WINDOW)

    def run_file(self):
        # Regenerate the input file
        success = self.generate_file()
        if not success:
            raise Exception("Could not generate data input file")

        to_run = self.current_file
        # I believe that this checks if it is using a relative path so that FCEA can reach it after the cwd change
        if self.current_file.startswith(DATA_FOLDER):
            to_run = "../" + to_run

        subprocess.run(f"echo {to_run} | \"FCEA2.exe\"", cwd="FCEA", shell=True, creationflags=CREATE_NO_WINDOW)

        # Display the output file
        self.outputs.update_display(self.read_output_file())


    def __init__(self, parent):
        super().__init__(parent)

        uniform = "input/output"
        self.grid_columnconfigure(0, weight=2, uniform=uniform)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1, uniform=uniform)

        self.grid_rowconfigure(0, weight=1)

        inputs_container = tk.Frame(self)
        inputs_container.grid(row=0, column=0, sticky="nsew")
        self.inputs: Inputs = Inputs(inputs_container)
        self.inputs.pack(fill=tk.BOTH, expand=True)
        self.bind_all('<Return>', lambda event : self.run_file())

        sep = ttk.Separator(self, orient=tk.VERTICAL)
        sep.grid(row=0, column=1, sticky="nsew")

        self.outputs: Outputs = Outputs(self)
        self.outputs.grid(row=0, column=2)

        run_button = tk.Button(inputs_container, text="ᐅ", command=self.run_file, font=("Helvetica", 20, "normal"))
        run_button.place(anchor=tk.SE, relx=1, rely=1)


        self.default_temp_file = f"{DATA_FOLDER}/.temp"
        self.set_current_file(self.default_temp_file)
        self.load_file(self.current_file_input)
        self.unsaved = True
        self.load_units()

        menu = tk.Menu(self)
        root.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)

        menu.add_cascade(label="File", menu=file_menu, underline=0)
        file_menu.add_command(label="New", command=self.new_file, underline=0, accelerator="Ctrl+N")
        self.bind_all("<Control-n>", lambda event : self.new_file())
        file_menu.add_command(label="Open", command=self.prompt_and_load_file, underline=0, accelerator="Ctrl+O")
        self.bind_all("<Control-o>", lambda event : self.prompt_and_load_file())
        file_menu.add_command(label="Save", command=self.save_current_file, underline=0, accelerator="Ctrl+S")
        self.bind_all("<Control-s>", lambda event : self.save_current_file())       
        file_menu.add_command(label="Save As", command=self.save_as_current_file, underline=5, accelerator="Ctrl+Shift+S")        
        self.bind_all("<Control-S>", lambda event : self.save_as_current_file())       
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=on_exit, underline=1, accelerator="Ctrl+Shift+Q")
        self.bind_all("<Control-Q>", lambda event : on_exit())# 

        run_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Run", menu=run_menu, underline=0)
        run_menu.add_command(label="Run CEA", command=self.run_file, underline=0, accelerator="<Enter>")
        # TODO: add buttons to optimize various things

        help_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Help", menu=help_menu, underline=0)
        help_menu.add_command(label="CEA", command=CEA_WINDOW)
        help_menu.add_command(label="Fuel", command=FUEL_WINDOW)
        help_menu.add_command(label="Oxidizer", command=OXIDIZER_WINDOW)
        help_menu.add_separator()
        help_menu.add_command(label="O/F", command=OF_WINDOW)
        help_menu.add_command(label="Chamber Pressure", command=PRESSURE_WINDOW)
        help_menu.add_command(label="Area Ratio", command=AREA_RATIO_WINDOW)
        help_menu.add_separator()
        help_menu.add_command(label="C*", command=CSTAR_WINDOW)
        help_menu.add_command(label="CF", command=CF_WINDOW)
        help_menu.add_command(label="Isp", command=ISP_WINDOW)

        # Add some units options in another dropdown here; maybe have some set everything imperial and metric functions. Would kind of suck because I have to make sure that everything that is already put in gets converted correctly
    
    def load_units(self):
        """Call on program load"""
        try:
            with open("./units.pkl", "ab+") as f: 
                f.seek(0)
                units = pickle.load(f)
        except EOFError: # if file is empty
            print("Units pickle is empty, ignoring")
        else:
            self.apply_units(units)

    def apply_units(self, selected_units):
        self.inputs.apply_units(selected_units)
        self.outputs.apply_units(selected_units)
    
    def save_units(self):
        """Call on program exit"""
        units = { **self.inputs.get_units(), **self.outputs.get_units() }

        with open("./units.pkl", "wb") as f: 
            pickle.dump(units, f)
    
    def set_current_file(self, new_path: str, has_been_saved=True):
        self.current_file = new_path
        self.update_title(has_been_saved)
    
    @property
    def current_file_input(self):
        return f"{self.current_file}.inp"
    
    @property
    def current_file_output(self):
        return f"{self.current_file}.out"


def on_exit():
    print("Attempting to exit")
    try:
        # Not calling
        editor.save_units()
    except Exception as e:
        print(traceback.format_exc())
    finally:
        root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    root.title(generate_name())
    root.iconbitmap("rocket.ico")
    images.initialize_images()

    editor = Editor(root)
    editor.pack(fill="both", expand=True)

    
    selected_units = {
        "pressure input": "bar",
    }

    def apply_selected_units():
        editor.apply_units(selected_units)

    root.state("zoomed")

    root.bind("<<Document-Altered>>", lambda *args: editor.set_unsaved())

    root.protocol("WM_DELETE_WINDOW", on_exit)
    root.mainloop()

    


