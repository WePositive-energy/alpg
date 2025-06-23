#!/usr/bin/python3

# Copyright (C) 2025 University of Twente

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# from configLoader import *
# config = importlib.import_module(cfgFile)
import random
import typer
from typing import Annotated
from pathlib import Path
from alpg.configLoader import config

from alpg import neighbourhood
from alpg.writer import OUTPUT_FILES

app = typer.Typer()


@app.command()
def main(
    cfgFile: Annotated[
        Path,
        typer.Option(
            "-c",
            "--config",
            help="",
            file_okay=True,
            dir_okay=False,
            readable=True,
            exists=True,
        ),
    ],
    output_name: Annotated[
        str,
        typer.Option(
            "-o",
            "--output",
            help="The subfolder in --output-folder to save the data in.",
        ),
    ] = "output",
    output_folder: Annotated[
        Path,
        typer.Option(
            help="The output directory to write to. Must be empty unless --force is specified.",
            file_okay=False,
            dir_okay=True,
            exists=True,
        ),
    ] = "output",
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", help="Overwrite any files in the --output directory."
        ),
    ] = False,
):
    print("Profilegenerator 2.0\n", flush=True)
    print("Copyright (C) 2025 University of Twente+WePositive.energy", flush=True)
    print("This program comes with ABSOLUTELY NO WARRANTY.", flush=True)
    print(
        "This is free software, and you are welcome to redistribute it under certain conditions.",
        flush=True,
    )
    print("See the acompanying license for more information.\n", flush=True)
    outputFolder = output_folder / output_name

    if not outputFolder.exists():
        outputFolder.mkdir()
    if len(list(outputFolder.iterdir())) != 0:
        if not force:
            print(
                "Config directory is not empty! Provide the --force flag to delete the contents",
                flush=True,
            )
            exit()
        for file in outputFolder.iterdir():
            if file.name in OUTPUT_FILES:
                file.unlink()

    config.load_config(cfgFile=cfgFile, outputFolder=outputFolder)
    config.generate_households()

    print("Loading config: " + str(cfgFile), flush=True)
    print(
        "The current config will create and simulate "
        + str(len(config.householdList))
        + " households",
        flush=True,
    )
    print("Results will be written into: " + str(outputFolder) + "\n", flush=True)
    print("NOTE: Simulation may take a (long) while...\n", flush=True)

    # Check the config:
    if config.penetrationEV + config.penetrationPHEV > 100:
        print("Error, the combined penetration of EV and PHEV exceed 100!", flush=True)
        exit()
    if config.penetrationPV < config.penetrationBattery:
        print(
            "Error, the penetration of PV must be equal or higher than PV!", flush=True
        )
        exit()
    if config.penetrationHeatPump + config.penetrationCHP > 100:
        print(
            "Error, the combined penetration of heatpumps and CHPs exceed 100!",
            flush=True,
        )
        exit()

    # Randomize using the seed
    random.seed(config.seed)

    # Create empty files
    config.writer.createEmptyFiles()

    neighbourhood.neighbourhood()

    hnum = 0

    householdList = config.householdList
    numOfHouseholds = len(householdList)

    while len(householdList) > 0:
        print("Household " + str(hnum + 1) + " of " + str(numOfHouseholds), flush=True)
        householdList[0].simulate()

        # Warning: On my PC the random number is still the same at this point, but after calling scaleProfile() it isn't!!!
        householdList[0].scaleProfile()
        householdList[0].reactivePowerProfile()
        householdList[0].thermalGainProfile()

        config.writer.writeHousehold(householdList[0], hnum)
        config.writer.writeNeighbourhood(hnum)

        householdList[0].Consumption = None
        householdList[0].Occupancy = None
        for p in householdList[0].Persons:
            del p
        del householdList[0]

        hnum = hnum + 1


if __name__ == "__main__":
    app()
