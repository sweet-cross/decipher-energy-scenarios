# decipher-energy-scenarios
Repository for the energy hackdays 2025 for the challenge: 

**Decipher Energy Scenarios**


## Get started

### Using Docker (Recommended)

The easiest way to run this project is using Docker Compose:

1. Install Docker and Docker Compose:
   - [Get Docker](https://docs.docker.com/get-docker/)
   - Docker Compose is included with Docker Desktop for Windows and Mac

2. Clone this repository and navigate to the project directory

3. Start the services using Docker Compose:
   ```bash
   docker compose up -d
   ```

4. Access the Jupyter notebooks at [http://localhost:8888](http://localhost:8888)

5. To stop the services:
   ```bash
   docker compose down
   ```

## Folder Structure

```
decipher-energy-scenarios/
├── .gitignore
├── .python-version
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── docker/
│   ├── NotebookDockerfile
│   ├── requirements_notebook.txt
│   └── data/
├── data/
│   ├── reports/
│   ├── scenario_results/
│   └── extracted/
└── notebooks/
```

- `data/`: Contains data files and results
  - `reports/`: PDF Files with the reports on the [`Energieperspektiven 2050+`](https://www.bfe.admin.ch/bfe/de/home/politik/energieperspektiven-2050-plus.html)
  - `scenario_results/`: Excel files with the numeric scenario results [`Energieperspektiven 2050+`](https://www.bfe.admin.ch/bfe/de/home/politik/energieperspektiven-2050-plus.html)
  - `extracted/`: CSV files with the data extracted from the original sources. Each table is named after the original table and contains the scenario and variant as additional dimension.
- `docker/`: Docker configuration files and persistent data
- `notebooks/`: Jupyter notebooks for data extraction, analysis, and exploration
- `pyproject.toml`: Project configuration and dependencies

## Docker Setup

The Docker Compose configuration includes:

- **Jupyter Notebook Server**: Accessible at [http://localhost:8888](http://localhost:8888)
- **PostgreSQL Database**: For storing and querying extracted data
- **Ollama**: For running AI models locally

Data for both PostgreSQL and Ollama is stored in the `docker/data` directory, making it persistent across container restarts.

## Working with the Notebooks

Once the Docker environment is running, you can access the Jupyter notebook server at [http://localhost:8888](http://localhost:8888). The following notebooks are available:

1. **extract_pdf_data.ipynb**: Extract data from PDF reports
2. **source_data_extraction_synthesis.ipynb**: Process and synthesize extracted data
3. **source_data_extraction_transformation.ipynb**: Transform data for analysis

The notebooks have access to all the data in the `data` directory and can save extracted information to the PostgreSQL database.
