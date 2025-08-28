import re
import pandas as pd


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
    df = (
        df.set_index(df.columns[:nr_index].to_list())
        .rename_axis(columns=name_years)
        .stack()
        .to_frame(name=name_values)
        .reset_index()
    )
    return df
