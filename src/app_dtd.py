#!/usr/bin/env python3
# coding: utf-8

import pandas as pd
import seaborn as sns
import numpy as np
import cyclopts # This 3rd-party package should be included in the environment.yml file pip section.
from pathlib import Path # This Python Standard Library package should not be added to environment.yml.
import geopandas as gpd
from shapely.geometry import Point


app = cyclopts.App(
    help="Help string for this app.",
    config=cyclopts.config.Json(
        "app_dtd_config.json",  # Use this file, if in cwd (or a parent).
        search_parents=True,
        )
    )


def get_population(config):
    ## Population data 
    pop_dir = f"{config['general_population_path']}{config['us_state']}"
    person_file = pop_dir+f"/base_population/{config['us_state']}_person.csv"
    hhold_file = pop_dir+f"/base_population/{config['us_state']}_household.csv"
    hloc_file = pop_dir+f"/home_location_assignment/{config['us_state']}_household_residence_assignment.csv"


    
     # Map out all files in /scif directory
    scif_path = Path('/scif/data/pop/va')
    if scif_path.exists():
        scif_files = [f.name for f in scif_path.iterdir() if f.is_file()]
        print(f'Files in /scif: {scif_files}')
        # Recursively show structure
        for item in scif_path.iterdir():
            if item.is_dir():
                subfiles = [f.name for f in item.iterdir() if f.is_file()]
                print(f'  {item.name}/: {subfiles}')
    else:
        print('/scif/data/pop/va directory does not exist')
    
    print(f'configuration: {config}')

    #### Load person and households data
    print(f'Laoding population file: {person_file}')
    person = pd.read_csv(person_file)
    print(f'Laoding population file: {hhold_file}')
    hhold = pd.read_csv(hhold_file)

    ## Home location data
    print(f'Laoding home location file: {hloc_file}')
    home_loc = pd.read_csv(hloc_file)
    pop = person.merge(home_loc[['hid','blockgroup_id']])

    print(f'Population from {config["us_state"]} is size: {pop.shape[0]}')
    return pop

def load_shapefile(config):
    shapefile_path = "../data/wastewaterscan_polygons_extracted.shp"
    polygons_gdf = gpd.read_file(shapefile_path)

    print(f"Loaded {len(polygons_gdf)} polygons from shapefile")
    print(f"CRS: {polygons_gdf.crs}")
    polygons_gdf.head()

## def load_activity_locations(config):


@app.default
def main(
    # Add config parameters here:
    us_state: str = "va",
    general_population_path: str = "/scif/data/pop/",
    population_path: str = "/project/bii_nssac/production/detailed_populations/ver_2_4_0/va",
    shapefile_path: str = "/scif/data"
    ):
    """
    This is the default function called when the script
    is run from the command line. You can put any lines
    of code you might normally have globally in a
    simple Python "script" here.

    Parameters
    ----------
    us_state: str
        lowercase two-letter state abbreviation to select which US population to access
    general_population_path: str
        The root directory for storing the population digital twins
    
    """

    config = {
        'us_state': us_state,
        'general_population_path': general_population_path,
        'population_path': population_path,
        'shapefile_path': shapefile_path
    }

    print(f'configuration: {config}')
    pop = get_population(config)

    print(f'Population from {config["us_state"]} is size: {pop.shape[0]}')

    # outpath = Path(outdir)
    # outpath.mkdir(exist_ok=True, parents=True)
    # outpath /= "main_output.txt"
    # output = f"{name}'s age is {age}.\n"
    # print(output)
    # with outpath.open("w") as filehandle:
    #     filehandle.write(output)
    # return output


if __name__ == "__main__":
    app()
