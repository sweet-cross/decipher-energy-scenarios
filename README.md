# decipher-energy-scenarios
Repository for the energy hackdays 2025 for the challenge: 

**Decipher Energy Scenarios**


## Get started

The project uses `uv` for dependency management. To use [`uv`](https://docs.astral.sh/uv/) 
in this project, follow these steps:

1. Install `uv` by following the instructions on the [official `uv` installation page](https://docs.astral.sh/uv/getting-started/).
2. Install the current state of the environment (including all dependency groups):
   ```bash
   uv sync --all-groups
   ```
3. Add dependencies to the project using the `uv add` command. For example:
   ```bash
   uv add <package-name>
   ```

## Folder Structure

```
decipher-energy-scenarios/
├── .gitignore
├── .python-version
├── README.md
├── pyproject.toml
├── uv.lock
├── data/
│   ├── reports/
│   └── scenario_results/
│   └── extracted/
└── notebooks/
```

- `data/`: Contains data files and results
  - `reports/`: PDF Files with the reports on the [`Energieperspektiven 2050+`](https://www.bfe.admin.ch/bfe/de/home/politik/energieperspektiven-2050-plus.html)
  - `scenario_results/`: Excel files with the numeric scenario results [`Energieperspektiven 2050+`](https://www.bfe.admin.ch/bfe/de/home/politik/energieperspektiven-2050-plus.html)
  - `extracted/`: CSV files with the data extracted from the original sources. Each table is named after the original table and contains the scenario and variant as additional dimension.
- `notebooks/`: Jupyter notebooks for data extraction, analysis, and exploration
- `pyproject.toml`: Project configuration and dependencies
- `uv.lock`: Locked dependency versions
