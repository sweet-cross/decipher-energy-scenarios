import re
from typing import Callable
import pandas as pd
from zipfile import ZipFile
import logging


dir_data = "../data/scenario_results/"
all_scenarios = {
    "ZERO-Basis": f"{dir_data}/10434-EP2050+_Szenarienergebnisse_ZERO-Basis.zip",
    "ZERO-A": f"{dir_data}/10435-EP2050+_Szenarienergebnisse_ZERO-A.zip",
    "ZERO-B": f"{dir_data}/10438-EP2050+_Szenarienergebnisse_ZERO-B.zip",
    "ZERO-C": f"{dir_data}/10439-EP2050+_Szenarienergebnisse_ZERO-C.zip",
    "WWB": f"{dir_data}/10440-EP2050+_Szenarienergebnisse_WWB.zip",
}


def parse_cell_reference(cell_ref: str) -> tuple[str, int]:
    """Parses an Excel cell reference (e.g., 'AZ102') into column and row.

    Args:
        cell_ref (str): The Excel cell reference to parse. E.g. AZ100

    Returns:
        tuple[str, int]: A tuple containing the column (str) and row (int) of the cell reference.

    """
    match = re.match(r"([A-Z]+)(\d+)", cell_ref.upper())
    if not match:
        raise ValueError(f"Invalid cell reference: {cell_ref}")

    column, row = match.groups()
    return column, int(row)


def df_from_excel(
    fn: str,
    start_cell: str,
    end_cell: str,
    sheet_name: str | None,
    nr_index: int | None = None,
    name_years: str = "year",
    name_values: str = "value",
    name_index: list[str] | None = None,
) -> pd.DataFrame:
    """Read a table from excel sheet using a reference for the start and
    end cell

    Args:
        fn (str): The file name of the Excel file.
        start_cell (str): The starting cell reference (e.g., 'A1').
        end_cell (str): The ending cell reference (e.g., 'B2').
        sheet_name (str | None): The name of the sheet to read from (default is None).
        nr_index (int): The number of index columns to read
            If there is an empty column in the dataframe read from excel, it is
            dropped. Thus the number of indexes should only count the columns.
            If not provided, the number of index columns will be inferred from the
            data, i.e., searching for the first column with a year entry
        name_years (str): The name to use for the columns in the resulting DataFrame.
            By default: year
        name_values (str): The name to use for the values in the resulting DataFrame.
            By default: value
        name_index (list[str] | None): The names to use for the index columns in
            the resulting DataFrame.
            By default: None

    Returns:
        pd.DataFrame: The resulting DataFrame containing the extracted table.
    """
    # parse the cell reference
    start_col, start_row = parse_cell_reference(start_cell)
    end_col, end_row = parse_cell_reference(end_cell)
    rows_to_skip = start_row - 1
    num_rows_to_read = end_row - start_row
    cols_to_use = f"{start_col}:{end_col}"

    df = (
        pd.read_excel(
            fn,
            sheet_name=sheet_name,
            usecols=cols_to_use,
            skiprows=rows_to_skip,
            nrows=num_rows_to_read,
            index_col=None,
            engine="openpyxl",
        )
        # drop columns that are completely empty
        .dropna(axis=1, how="all")
    )

    # parse indexes
    if nr_index is None:
        # infer the first column with a valid year
        for i, col in enumerate(df.columns):
            try:
                first_year = int(col)
                if 1800 <= first_year <= 2100:
                    nr_index = i
                    break
            except Exception:
                continue
        if nr_index is None:
            raise ValueError("Could not infer the number of index columns.")
    df = df.set_index(df.columns[:nr_index].to_list()).rename_axis(columns=name_years)
    if name_index is not None:
        df.index.names = name_index if isinstance(name_index, list) else [name_index]
    df = df.stack().to_frame(name=name_values).reset_index()
    return df


def extract_data_all_scenarios(
    sheet_name: str,
    fn_excel: Callable,
    start_cell: str,
    end_cell: str,
    nr_index: int | None = None,
    name_values: str = "value",
    name_years: str = "year",
    name_index: str | list[str] | None = None,
    exclude_scenarios: list[str] | None = None,
) -> pd.DataFrame:
    """Extract a table for all scenarios

    Args:
        sheet_name (str): The name of the sheet within the excel file
        fn_excel (Callable): The name of the excel file in the zip archive. This should
            be a callable that depends on the scenario name
            E.g.: fn_excel = lambda x: f"EP2050+_Szenarienergebnisse_{x}/EP2050+_Ergebnissynthese_2020-2060_{x}_KKW50_ausgeglicheneJahresbilanz_2022-04-12.xlsx"
        start_cell (str): The starting cell of the table to extract (e.g., "A1")
        end_cell (str): The ending cell of the table to extract (e.g., "D10")
        nr_index (int | None): The number of index columns to use
        name_values (str): The name for the column that contains the values
        name_years (str): The name for the column that contains the years
        name_index (str | list[str] | None): The names to use for the index columns in
            the resulting DataFrame.
        exclude_scenario (list[str] | None): A list of scenario names to exclude from the
            extraction process.

    Returns:
        pd.DataFrame: The extracted table as a pandas DataFrame
    """
    if exclude_scenarios is None:
        exclude_scenarios = []
    scenarios = {k: v for k, v in all_scenarios.items() if k not in exclude_scenarios}
    lst_df = []
    for scenario, fn_zip in scenarios.items():
        print(f"Extracting data for scenario {scenario}")
        # the zip file with the scenario results
        with ZipFile(fn_zip, "r") as zip_file:
            # the excel in the zip file
            fn_xls = fn_excel(scenario)
            if fn_xls not in zip_file.namelist():
                logging.warning(f"{fn_xls} not found in {fn_zip}")
                continue
            with zip_file.open(fn_xls) as excel_file:
                df = df_from_excel(
                    fn=excel_file,
                    sheet_name=sheet_name,
                    start_cell=start_cell,
                    end_cell=end_cell,
                    nr_index=nr_index,
                    name_values=name_values,
                    name_years=name_years,
                    name_index=name_index,
                )
                lst_df.append(df.assign(scenario=scenario))
    df = pd.concat(lst_df, ignore_index=True)
    return df


map_tech = {
    "Wasserkraftwerke": "hydro",
    "bestehende Wasserkraft": "hydro_existing",
    "neue Wasserkraft": "hydro_new",
    "Kernkraftwerke": "nuclear",
    "bestehende Kernkraftwerke": "nuclear_existing",
    "neue Kernkraftwerke": "nuclear_new",
    "Fossile KW (gekoppelt und ungekoppelt)": "fossil",
    "bestehende fossile KW": "fossil_existing",
    "neue Kombikraftwerke": "ccpp_new",
    "neue KW fossil/PtG": "fossil_new",
    "Übrige Erneuerbare (gekoppelt und ungekoppelt)": "renewable",
    "bestehende Erneuerbare": "renewable_existing",
    "neue Erneuerbare (inkl. abgeregelte EE)": "renewable_new",
    "Mittlere Bruttoerzeugung": "generation_gross",
    "Verbrauch der Speicherpumpen": "storage",
    "Mittlere Nettoerzeugung": "generaion_net",
    "Importsaldo (Importe minus Exporte)": "net_import",
    "bestehende Bezugsrechte": "subscription_rights",
    "bestehende Lieferverpflichtungen": "obligations",
    "Landesverbrauch": "gross_consumption",
    "davon Verluste": "losses",
    "Bruttoverbrauch": "net_consumption",
}

map_res = {
    "Photovoltaik": "solar",
    "Windenergie": "wind",
    "Biomasse (Holz)": "wood",
    "Biogas": "biogas",
    "ARA": "waste_gas",
    "KVA (EE-Anteil)": "waste_renewable",
    "Geothermie": "geothermal",
    "Erneuerbare gesamt (ohne EE-Abregelung)": "gross_renewable",
    "EE-Abregelung": "curtailment",
}
