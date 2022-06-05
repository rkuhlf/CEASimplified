
import tkinter as tk


def helpWindow(title="Help", message="Not yet implemented."):
    win = tk.Toplevel(padx=50, pady=20)

    win.title(title)

    screen_width = win.winfo_screenwidth()
    window_width = int(screen_width * 0.35)

    screen_x = screen_width // 2 - window_width // 2
    screen_y = 100

    win.geometry(f"+{screen_x}+{screen_y}")


    tk.Label(win, text=message, wraplength=int(window_width*0.75)).pack(fill="y", expand=True)
    tk.Button(win, text='Okay', command=win.destroy).pack(pady=(30, 0))


GENERAL_CEA_MESSAGE = "CEA stands for chemical equilibrium analysis. It determines the outcome of chemical reactions by assuming that the reactants (propellants, in this case) are allowed to sit for an infinitely long amount of time, allowing the reaction to proceed until it reaches an equilibrium. This is relatively accurate for a rocket because there is so much energy bouncing around the combustion chamber that reactions occur very quickly.\n\nIn the 60s NASA developed their own CEA program, coded in Fortran. Some versions of it have been publicly released, which you can probably still find online by searching for \"NASA CEA.\" This app is a wrapper for that NASA program, providing a simplified user interface but using the same underlying Fortran program developed so long ago.\n\nIdeally, you can use it to quickly test out combinations of propellant, determining the optimal O/F ratio at pressure and eventually calculating the thrust of your rocket."
CEA_WINDOW = lambda : helpWindow("What is CEA Simplified?", GENERAL_CEA_MESSAGE)

OF_MESSAGE = "O/F stands for the oxidizer to fuel ratio, calculated by dividing the mass of oxidizer by the mass of fuel. This is the key parameter in determining how effective the combustion in your engine is - if there is too much fuel or oxidizer, then it will be left unburnt, decreasing the amount of thrust you get for the amount of propellant loaded.\n\nHowever, there are several factors apart from thrust that impact the best O/F for a rocket. The more oxidizer there is, the more likely an oxidation reaction will occur in your combustion chamber or nozzle (depending on materials). A larger O/F also will typically burn cooler, possibly allowing a lighter rocket with less thermal protection. The volume of propellant can also affect the ultimate decision: If one of your propellants is extremely dense, it may make more sense to load a relatively larger mass of that propellant into the rocket so that you can have more propellant for less overall length."
OF_WINDOW = lambda : helpWindow("What is an O/F ratio?", OF_MESSAGE)

PRESSURE_MESSAGE = "The pressure of the combustion chamber (measured in absolute pounds per square inch) has some influence on the chemistry of combustion. Like any reaction, the equilibrium that is ultimately established is dependant on Le Chatelier's Principle (at higher pressures, equilibrium tends to shift to the side of an equation with fewer gaseous molecules). That being said, the chemistry gets to be quite complicated, as the enthalpy of formation also varies with the pressure for each chemical. Regardless of theoretical complexity, higher combustion chamber pressures tend to give more efficient rockets.\n\nA larger chamber pressure also gives you a bigger pressure ratio between internal and atmospheric conditions, so it requires a larger area ratio in the nozzle. Accordingly, upper stage engines frequently have lower chamber pressures, since the pressure ratio already approaches infinity.\n\nCombustion chamber pressure is usually calculated with estimations before running CEA (although, like everything, it creates a bit of a feedback loop) by solving the characteristic velocity equation (using an estimate for C*, usually 1500-2000 m/s) using a known mass flow rate of oxidizer and fuel."
PRESSURE_WINDOW = lambda : helpWindow("Importance of combustion chamber pressure", PRESSURE_MESSAGE)

AREA_RATIO_MESSAGE = "Area ratio (often abbreviated with an epsilon, ε) refers to the cross sectional area at the nozzle exit divided by the cross sectional area at the nozzle throat. It is usually optimized so that the pressure at the exit of the nozzle is as close as possible to the ambient pressure, as that most efficiently converts energy from pressure into thrust. As the chamber pressure increases or the ambient pressure decreases, the area ratio should decrease."
AREA_RATIO_WINDOW = lambda : helpWindow("What is an area ratio?", AREA_RATIO_MESSAGE)

CSTAR_MESSAGE = "Despite being in velocity units, characteristic velocity (often C*) does not represent any physical motion. Instead, it is calculated by multiplying the mass flow rate and the combustion chamber pressure together, then dividing by the area of the throat. This creates a value that is indicative of efficiency of the combustion independent of the nozzle. Typical values range from 1500 to 2000 m/s."
CSTAR_WINDOW = lambda : helpWindow("What is Characteristic Velocity?", CSTAR_MESSAGE)
ISP_MESSAGE = "Isp represents the specific impulse of a propellant combination. Impulse refers to a change in momentum, or the total thrust in a period of time. Specific simply means that it is divided by mass. However, weight is used rather than mass to make it nearly dimensionless, allowing for easy comparison between metric and imperial systems (you will still see some usage where it is divided by mass, so be sure to double check if comparisons are off by a large margin).\n\nSpecific impulse is a measure of effeciency for the entire propulsion system, i.e. the higher your specific impulse the better your rocket is. Different propellant combinations will each have their own range of typical specific impulse, but this is the value that should be used to optimize the O/F ratio."
ISP_WINDOW = lambda : helpWindow("What is Specific Impulse?", ISP_MESSAGE)
CF_MESSAGE = "CF represents the nozzle thrust coefficient, the multiplicative benefit that the nozzle provides in terms of thrust. Mathematically, it says that a rocket is CF times as effective because of the nozzle. As you optimize the area ratio of the nozzle, the CF should increase. If it is below one, there is probably a major issue somewhere."
CF_WINDOW = lambda : helpWindow("What is a Nozzle Coefficient?", CF_MESSAGE)

PROPELLANT_MESSAGE = "Rocket propellant refers to the chemicals that drive the combustion in the rocket. Like combustion in a regular fire, combustion in a rocket requires fuel, oxygen, and energy. CEA assumes that there is sufficient energy to ignite the reaction and to maintain it to completion, so it only requires fuel and oxidizer inputs.\n\nIn general, rocket propellant has a single purpose: take stored chemical energy and transform it into pressure energy. That effectiveness is dependent solely on the flame temperature and the molar mass of products. The more energy the reaction gives off, the hotter it will be, and that higher temperature will give an increased pressure. If your reactants have a bigger heat/enthalpy of formation, they will have more energy to release when reacted. Likewise, if the particles that are created are smaller (i.e. lower molar mass), there will be more of them bouncing around causing an increased pressure."

FUEL_MESSAGE = PROPELLANT_MESSAGE + "\n\nRocket fuel takes many forms, but it is usually an organic compound that has a lot of hydrogen so that the combustion reaction can effectively produce water (H2O). As the size of the compounds gets larger, carbon is frequently incorporated to maintain the longer chains. Unfortunately, carbon will typically only react to form carbon dioxide, which is a much less energetic reaction than forming water.\n\nAs those chains get longer, eventually fuels turn into liquids and solids. For most fuels, they would be categorized as polymers at this point, as options like HTPB or ABS consist of long carbon chains created by polymerization reactions. It is difficult to characterize the heat of formation for such a polymer, because the exact chemical formula will be slightly different even between batches, and significantly different between different processes."
FUEL_WINDOW = lambda : helpWindow("How Does Rocket Fuel Work?", FUEL_MESSAGE)

OXIDIZER_MESSAGE = PROPELLANT_MESSAGE + "\n\nRocket oxidizer does not necessarily have to include oxygen in the chemical formula, but it should include chemicals that behave like oxygen. In the chemical reaction, the oxidizer will typically try to take some of the hydrogen atoms from the fuel, causing it to decompose but also creating compounds that release more energy. Fluorine, for example, behaves similarly to oxygen because it is highly electronegative and eager to bond with hydrogen, so it functions well as an oxidizer.\n\nThere are fewer options for oxidizer than there are for fuel, and each one offers its own problems and solutions. Fluorine is usually most chemically efficient, but it is extremely hazardous. Hydrogen peroxide (H2O2) is a typical starting point, and nitrous (N2O) is good because it is self-pressurizing. Jet engines just use air from the atmosphere, primarily reacting the fuel with the 21% that is oxygen. That being said, once you get to larger liquid rockets, almost all of them are designed with liquid oxygen."
OXIDIZER_WINDOW = lambda : helpWindow("How Does Rocket Oxidizer Work?", OXIDIZER_MESSAGE)

    