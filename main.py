# TODO: Deploy to Github and SourceForge, add a link in the notes for future Goddard
# TODO: Make unit conversion dropdowns everywhere, include a list of the units and their conversion factors in the parameters
# TODO: add an asterisk to the title bar if you have not saved your most recent change (probably will be sucky)
# TODO: figure out why increasing the area ratio always gives a better Isp
# TODO: install UPX so that pyinstaller can compress .exe files

import os
import re
import subprocess

import tkinter as tk
from tkinter import filedialog as fd
from tkinter import CENTER, LEFT, RIGHT, ttk
from tkinter import messagebox
from HelpWindow import AREA_RATIO_MESSAGE, AREA_RATIO_WINDOW, CEA_WINDOW, CF_MESSAGE, CF_WINDOW, CSTAR_MESSAGE, CSTAR_WINDOW, FUEL_MESSAGE, FUEL_WINDOW, ISP_MESSAGE, ISP_WINDOW, OF_MESSAGE, OF_WINDOW, OXIDIZER_MESSAGE, OXIDIZER_WINDOW, PRESSURE_MESSAGE, PRESSURE_WINDOW, helpWindow, GENERAL_CEA_MESSAGE
from PropellantSelect import CompoundSelect
import os.path

from fonts import title_font, subtitle_font

from typing import List

from Exceptions import PresetException, UnknownCEAException, UserInputException

from compound import CustomCompound, PresetCompound
from helperWidgets import LabeledInput, LabeledOutput, help_button
import images

data_folder = "./CEAData"
fcea_folder = "./FCEA"
CREATE_NO_WINDOW = 0x08000000

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
    def __init__(self, parent):
        super().__init__(parent)

        help_wrapper = tk.Frame(self)
        help_wrapper.pack(pady=(0, 40))
        tk.Label(help_wrapper, text="CEA Simplified", font=title_font).pack(side=tk.LEFT)
        help_button(help_wrapper, command=CEA_WINDOW).pack(padx=(5, 0), side=tk.RIGHT)

        text_inputs = tk.Frame(self)
        text_inputs.pack(pady=20)

        # TODO: Add an optimize button next to it. Also requires decoupling the simulation code. And making it a grid layout
        # Use 🗲 as icon
        self.OF_input = LabeledInput(text_inputs, "O/F (): ", numerical=True, uniform="main", help_func=OF_WINDOW)
        self.OF_input.pack()

        self.pressure_input = LabeledInput(text_inputs, "Pressure (psia): ", numerical=True, uniform="main", help_func=PRESSURE_WINDOW)
        self.pressure_input.pack()

        self.area_ratio_input = LabeledInput(text_inputs, "Area Ratio (): ", numerical=True, uniform="main", help_func=AREA_RATIO_WINDOW)
        self.area_ratio_input.pack()

        sep = ttk.Separator(self, orient=tk.HORIZONTAL)
        sep.pack(fill="x")
        
        self.propellants_frame = tk.Frame(self)
        self.propellants_frame.pack(fill=tk.X)
        self.propellants_frame.grid_columnconfigure(0, weight=1, uniform="propellant_column")
        self.propellants_frame.grid_columnconfigure(2, weight=1, uniform="propellant_column")

        padding: float = 20

        self.fuel_select = CompoundSelect(self.propellants_frame, name="Select Fuel", preset_compound_options=["CH4", "H2", "RP-1"], help_func=FUEL_WINDOW)
        self.fuel_select.grid(row=0, column=0, padx=padding, sticky="ne")

        sep = ttk.Separator(self.propellants_frame, orient=tk.VERTICAL)
        sep.grid(row=0, column=1, sticky="nsew")

        self.oxidizer_select = CompoundSelect(self.propellants_frame, name="Select Oxidizer", preset_compound_options=["Air", "H2O2(L)", "N2O", "O2", "CL2", "F2", "N2H4(L)"], help_func=OXIDIZER_WINDOW)
        self.oxidizer_select.grid(row=0, column=2, padx=padding, sticky="nw")

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
            return float(self.pressure_input.value)
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

    # Wow object-oriented programming gets sucky in a hurry
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
    def pack_row(self, parent, values: "List[str]"=[], start_col=0, row=0, **kwargs):
        for index, val in enumerate(values):
            label = tk.Label(parent, text=val)
            label.grid(row=row, column=start_col+index, **kwargs)

    def pack_conditions(self, new_outputs={}):
        self.conditions = tk.Frame(self)
        self.conditions.pack()

        row_title_offset = 5
        self.pack_row(self.conditions, ["Chamber", "Throat", "Exit"], start_col=1, sticky="e", pady=(0, 5))
        self.pack_row(self.conditions, ["Pressure (atm)"], start_col=0, row=1, sticky="w", padx=row_title_offset)
        self.pack_row(self.conditions, ["Temperature (°C)"], start_col=0, row=2, sticky="w", padx=row_title_offset)
        self.pack_row(self.conditions, ["Density (kg/m^3)"], start_col=0, row=3, sticky="w", padx=row_title_offset)
        self.pack_row(self.conditions, ["Mach Number ()"], start_col=0, row=4, sticky="w", padx=row_title_offset)
        self.pack_row(self.conditions, ["Velocity (m/s)"], start_col=0, row=5, sticky="w", padx=row_title_offset)

        if new_outputs:
            velocities = []
            for sonic, mach in zip(new_outputs["sonicVelocity"], new_outputs["mach"]):
                new_velocity = float(sonic) * float(mach)
                velocities.append(f"{new_velocity:.0f}")
            

            def round_str(arr, n=0):
                return list(map(lambda p : str(round(p, n)), arr))
            
            pressures = round_str(new_outputs["pressure"], 1)
            temperature = round_str(new_outputs["temperature"], 0)
            density = round_str(new_outputs["density"], 4)
            mach = round_str(new_outputs["mach"], 2)
            self.pack_row(self.conditions, pressures, start_col=1, row=1, sticky="e")
            self.pack_row(self.conditions, temperature, start_col=1, row=2, sticky="e")
            self.pack_row(self.conditions, density, start_col=1, row=3, sticky="e")
            self.pack_row(self.conditions, mach, start_col=1, row=4, sticky="e")
            self.pack_row(self.conditions, velocities, start_col=1, row=5, sticky="e")

    def update_display(self, new_outputs):
        self.cstar_display.update_value(str(round(float(new_outputs["cstar"]))))
        self.CF_display.update_value(str(round(float(new_outputs["CF"]), 3)))
        self.Isp_display.update_value(str(round(float(new_outputs["Isp"]))))

        self.conditions.destroy()
        self.pack_conditions(new_outputs)

    def __init__(self, parent):
        super().__init__(parent)

        subtitle_offset = 0
        self.performance_label = tk.Label(self, text="Propulsion Characteristics")
        self.performance_label.configure(font=subtitle_font)
        self.performance_label.pack(pady=(0, subtitle_offset))
        performance = tk.Frame(self)
        performance.pack()

        self.cstar_display = LabeledOutput(performance, prefix="Characteristic Velocity (m/s): ", help_func=CSTAR_WINDOW, uniform="outputs")
        self.cstar_display.pack()
        self.CF_display = LabeledOutput(performance, prefix="Nozzle Coefficient (): ", help_func=CF_WINDOW, uniform="outputs")
        self.CF_display.pack()

        self.Isp_display = LabeledOutput(performance, prefix="Specific Impulse (s): ", help_func=ISP_WINDOW, uniform="outputs")
        self.Isp_display.pack()


        self.conditions_label = tk.Label(self, text="Propulsion Conditions")
        self.conditions_label.configure(font=subtitle_font)
        self.conditions_label.pack(pady=(20, subtitle_offset))
        self.pack_conditions()

    def clear(self):
        self.Isp_display.clear()
        self.CF_display.clear()
        self.cstar_display.clear()

        self.conditions.destroy()
        self.pack_conditions()

filetypes = (
    ('CEA files', '*.inp'),
    ('All files', '*.*')
)

class Main(tk.Frame):
    def clear(self):
        self.inputs.clear()
        self.outputs.clear()

    def new_file(self):
        # set to temp and clear inputs
        self.set_current_file(self.default_temp_file)
        self.clear()

    def prompt_and_load_file(self):
        filename = fd.askopenfilename(
            title='Open an Input File',
            initialdir=f'./{data_folder}',
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
                    preset_selection = re.search(f"{prefix}=(\w*)", text)

                    if preset_selection:
                        select_object.is_custom = False
                        select_object.name = preset_selection.groups()[0]
                    else:
                        # It is not custom or preset (we found nothing)
                        select_object.clear()
            
            update_propellant_select("fuel", self.inputs.fuel_select)
            update_propellant_select("oxid", self.inputs.oxidizer_select)
            
    
    def save_as_current_file(self):
        name = fd.asksaveasfilename(
                title='Save as',
                initialdir=f'./{data_folder}',
                filetypes=filetypes)
        
        if not name:
            return
            
        self.set_current_file(name)

        self.save_file()

    def save_current_file(self):
        if self.current_file == self.default_temp_file:
            self.save_as_current_file()
        else:
            self.save_file()
    
    def save_file(self):
        # TODO: make a save function that does not require everything to be filled out
        self.generate_file()

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
                
                outputs["cstar"] = cstar.groups()[0]
                outputs["CF"] = cf.groups()[0]
                metric_Isp = metric_Isp.groups()[0]
                metric_Isp = float(metric_Isp)
                metric_Isp /= 9.81
                # Divide by the acceleration of gravity to get it in seconds
                outputs["Isp"] = str(metric_Isp)

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
                    # Convert from bar to atm
                    outputs[to_assign] = values
                
                process_column("P, BAR", "pressure", lambda pressure: pressure * 0.986923)
                process_column("T, K", "temperature", lambda temperature: temperature - 273.15)
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
            return

        to_run = self.current_file
        # I believe that this checks if it is using a relative path so that FCEA can reach it after the cwd change
        if self.current_file.startswith(data_folder):
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
        inputs_container.grid(row=0, column=0)
        self.inputs: Inputs = Inputs(inputs_container)
        self.inputs.pack()
        runButton = tk.Button(inputs_container, text="Run", command=self.run_file)
        runButton.pack(pady=20)
        self.bind_all('<Return>', lambda event : self.run_file())

        sep = ttk.Separator(self, orient=tk.VERTICAL)
        sep.grid(row=0, column=1, sticky="nsew")

        self.outputs: Outputs = Outputs(self)
        self.outputs.grid(row=0, column=2)


        self.default_temp_file = f"{data_folder}/.temp"
        self.set_current_file(self.default_temp_file)
        self.load_file(self.current_file_input)

        menu = tk.Menu(self)
        root.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)

        menu.add_cascade(label="File", menu=file_menu, underline=0)
        # Most of this stuff is just changing file names
        file_menu.add_command(label="New", command=self.new_file, underline=0, accelerator="Ctrl+N")
        self.bind_all("<Control-n>", lambda event : self.new_file())
        file_menu.add_command(label="Open", command=self.prompt_and_load_file, underline=0, accelerator="Ctrl+O")
        self.bind_all("<Control-o>", lambda event : self.prompt_and_load_file())
        file_menu.add_command(label="Save", command=self.save_current_file, underline=0, accelerator="Ctrl+S")
        self.bind_all("<Control-s>", lambda event : self.save_current_file())       
        file_menu.add_command(label="Save As", command=self.save_as_current_file, underline=5, accelerator="Ctrl+Shift+S")        
        self.bind_all("<Control-S>", lambda event : self.save_as_current_file())       
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit, underline=1, accelerator="Ctrl+Shift+Q")
        self.bind_all("<Control-Q>", lambda event : root.quit())

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
        
    
    def set_current_file(self, new_path: str):
        self.current_file = new_path
        if new_path == self.default_temp_file:
            root.title(f"{APPLICATION_NAME}")
        else:
            root.title(f"{APPLICATION_NAME} - {new_path}")
    
    @property
    def current_file_input(self):
        return f"{self.current_file}.inp"
    
    @property
    def current_file_output(self):
        return f"{self.current_file}.out"

        
if __name__ == "__main__":
    root = tk.Tk()
    APPLICATION_NAME = "CEA Simplified"
    root.title(APPLICATION_NAME)
    root.iconbitmap("rocket.ico")
    images.initialize_images()

    main = Main(root)
    main.pack(fill="both", expand=True)

    root.state("zoomed")

    root.mainloop()




# Have a help menu
# Maybe a troubleshooting page with some info
# I am pretty sure that having spaces anywhere in your path will screw it up beyond recognition

# edit menu includes the run button with a shortcut (probably enter)