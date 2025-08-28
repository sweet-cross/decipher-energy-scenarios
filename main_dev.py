from notebooks.utils import df_from_excel
from zipfile import ZipFile

if __name__ == "__main__":
    dir_data = "./data/scenario_results/"
    scenario = "ZERO-Basis"
    # the zip file with the scenario results
    fn_zip = f"{dir_data}/10434-EP2050+_Szenarienergebnisse_{scenario}.zip"

    with ZipFile(fn_zip, "r") as zip_file:
        # the excel in the zip file
        fn_excel = f"EP2050+_Szenarienergebnisse_{scenario}/EP2050+_Ergebnissynthese_2020-2060_{scenario}_KKW50_ausgeglicheneJahresbilanz_2022-04-12.xlsx"
        print(zip_file.namelist())
        with zip_file.open(fn_excel) as excel_file:
            # the sheet we want to read from
            sheet_name = "01 Annahmen und Rahmendaten"
            df = df_from_excel(
                fn=excel_file,
                sheet_name=sheet_name,
                start_cell="B12",
                end_cell="BM16",
                name_values="economic_assumptions",
            )
        pass
    print(df)
