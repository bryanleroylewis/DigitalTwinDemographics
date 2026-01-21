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
    pop = person.merge(home_loc[['hid','blockgroup_id','longitude','latitude']])

    print(f'Population from {config["us_state"]} is size: {pop.shape[0]}')
    return pop

def load_polygons_from_csv(config):
    from shapely.geometry import shape
    import ast
    
    print(f"Loading polygons from {config['csv_path']}")
    df = pd.read_csv(config['csv_path'])
    
    # Parse polygon coordinates and create geometries, skipping NaNs and invalid entries
    def parse_geometry(coord_str):
        try:
            if pd.isna(coord_str):
                return None
            coords = ast.literal_eval(coord_str)
            if not coords or len(coords) == 0 or len(coords[0]) < 3:
                return None
            return shape({'type': 'Polygon', 'coordinates': coords})
        except:
            return None
    
    df['geometry'] = df['polygon.coordinates'].apply(parse_geometry)
    
    # Filter out rows with invalid geometries
    polygons_gdf = gpd.GeoDataFrame(df[df['geometry'].notna()], geometry='geometry', crs="EPSG:4326")
    
    print(f"Loaded {len(polygons_gdf)} valid polygons from CSV (skipped {len(df) - len(polygons_gdf)} invalid entries)")
    print(f"CRS: {polygons_gdf.crs}")
    print(f"Shape: {polygons_gdf.shape}")
    return polygons_gdf


def get_pop_coords(config, pop):
    # Create GeoDataFrame from population data
    # Convert to Point geometries
    geometry = [Point(xy) for xy in zip(pop['longitude'], pop['latitude'])]
    pop_gdf = gpd.GeoDataFrame(pop, geometry=geometry, crs="EPSG:4326")

    print(f"Created GeoDataFrame with {len(pop_gdf)} population records")
    print(f"CRS: {pop_gdf.crs}")

    return pop_gdf

## def load_activity_locations(config):
def find_pop_in_polygons(config, pop_gdf, polygons_gdf):
    # Ensure both GeoDataFrames use the same CRS
    # polygons_gdf = polygons_gdf.to_crs(pop_gdf.crs)

    # Perform spatial join to find which population points fall within which polygons
    pop_in_polygons = gpd.sjoin(pop_gdf, polygons_gdf, how="inner", predicate="within")

    print(f"Found {len(pop_in_polygons)} population records within polygons")
    print("Population example:\n", pop_in_polygons.columns,"\n", pop_in_polygons.head())
    return pop_in_polygons

def count_population_by_category(pop_in_polygons, category_columns):
    # Count population by specified category
    category_counts = pop_in_polygons.groupby(category_columns).count().reset_index()

    return category_counts

@app.default
def main(
    # Add config parameters here:
    us_state: str = "va",
    general_population_path: str = "/scif/data/pop/",
    population_path: str = "/project/bii_nssac/production/detailed_populations/ver_2_4_0/va",
    csv_path: str = "/scif/data/site_polygons.csv"
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
    csv_path: str
        Path to the CSV file containing polygon information
    
    """

    config = {
        'us_state': us_state,
        'general_population_path': general_population_path,
        'population_path': population_path,
        'csv_path': csv_path
    }

    print(f'configuration: {config}')
    pop = get_population(config)

    print(f'Population size from {config["us_state"]}: {pop.shape[0]}')

    polygons_gdf = load_polygons_from_csv(config)
    pop_gdf = get_pop_coords(config, pop)
    pop_in_polygons = find_pop_in_polygons(config, pop_gdf, polygons_gdf)
    print(f'Population in polygons is size: {pop_in_polygons.shape[0]}')

    category_columns = ['place_name', 'race']
    category_counts = count_population_by_category(pop_in_polygons, category_columns)
    print("Population counts by category:\n", category_counts)

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
