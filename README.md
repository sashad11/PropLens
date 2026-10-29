# What I built and who for

**PropLens — London's air, through the spaces we use**

PropLens is a Python and SQL data engineering project that explores historical air pollution measurements near different types of buildings across London.

The project considers the populations who use these spaces, including children at schools, patients at hospitals, older residents in care homes, students at universities, office workers and people living in residential buildings.

Its purpose is to make environmental data more accessible and encourage consideration of air quality in relation to the people using different spaces.

PropLens currently examines six real London locations:

- Fox Primary School — School
- St Thomas' Hospital — Hospital
- Magnolia Court Care Home — Care home
- UCL North-West Wing — University
- 80 Strand — Commercial office
- Barbican Estate — Residential

**Important limitation:** PropLens does not measure pollution exposure inside individual buildings or assess personal health risks. It compares measurements from nearby monitoring stations, which may not represent conditions at the buildings themselves.

# The data

The project uses data from the **London Air Quality Network (LAQN)**, accessed through its public API:

https://api.erg.ic.ac.uk/AirQuality/help

The LAQN provides air pollution measurements from monitoring stations across London.

The current analysis primarily focuses on **nitrogen dioxide (NO₂)**, measured in micrograms per cubic metre (µg/m³). The pipeline also collects particulate matter (PM₂.₅) measurements for selected stations.

The main historical dataset covers **1 August to 27 October 2026**, with hourly readings from selected monitoring stations.

Data used in PropLens includes:

- **Raw API responses:** Original JSON files retained for traceability.
- **Station metadata:** Monitoring station names, coordinates, monitoring types and available pollutants.
- **Building locations:** A CSV containing six real London buildings, their types and approximate geographical coordinates.
- **Processed measurements:** Hourly pollution records stored in DuckDB.
- **Analysis outputs:** CSV reports showing air quality comparisons and monthly trends.

The building coordinates are approximate reference points. Some may represent a postcode or a wider estate rather than a specific entrance.

**Data attribution:** Air pollution measurements and monitoring station information are sourced from the London Air Quality Network. The project is an independent educational analysis and is not affiliated with LAQN. Users should refer to LAQN's published information and terms when reusing its data.

# How it works

PropLens follows an **extract, transform and load (ETL)** process.

**1. Extract**

Python requests historical hourly air pollution measurements from the LAQN API.

The collection script:

- Requests data for selected station–pollutant combinations.
- Saves original API responses as JSON files.
- Checks whether a daily file has already been downloaded before requesting it again.
- Introduces a delay between requests to avoid repeatedly contacting the API unnecessarily.

**2. Transform and load**

The loading script reads the saved JSON responses and processes the hourly observations.

It:

- Extracts station codes, pollutant codes, timestamps and measured values.
- Represents missing numerical measurements as SQL `NULL` values.
- Stores the processed records in a DuckDB database.
- Uses a primary key and conflict handling to prevent duplicate measurements.
- Tracks previously processed source files so unchanged files are not loaded repeatedly.

This allows the pipeline to be rerun without duplicating existing data.

**3. Check data quality**

PropLens examines the proportion of stored hourly measurements that contain valid numerical readings.

It uses project-defined completeness labels:

- **GOOD:** At least 95% numerical readings.
- **CAUTION:** At least 80%, but below 95%.
- **POOR:** Below 80%.

These are internal project thresholds, not official LAQN data-quality ratings.

The completeness calculation currently considers stored records. It does not fully identify timestamps that may be absent from the dataset.

**4. Match buildings to monitoring stations**

PropLens uses latitude and longitude coordinates and the Haversine formula to estimate straight-line distances between buildings and monitoring stations.

The project compares six building locations with selected stations that have collected historical data.

A separate exploration step identifies other nearby LAQN stations. These candidates are not automatically selected because proximity alone does not guarantee suitable or complete data.

For reporting, distances are labelled using provisional project guidelines:

- **NEARBY:** Up to 2 km.
- **CAUTION:** Over 2 km and up to 3 km.
- **DISTANT:** Over 3 km.

These labels are not scientific thresholds for pollution exposure.

**5. Analyse and export**

DuckDB SQL queries combine building matches with historical monitoring measurements.

The project produces two main reports:

- `Outputs/property_comparison.csv` — Average NO₂, building type, monitoring station, distance, completeness and warnings.
- `Outputs/monthly_trends.csv` — Monthly average NO₂ and the number of valid and recorded hourly measurements.

The comparison report also identifies buildings that share the same station, so identical measurements are not presented as independent evidence.

**Current limitations**

The six buildings are currently matched to three distinct NO₂ monitoring stations. Four buildings share station CE3.

Two buildings have monitoring stations more than 3 km away, so their results require particular caution.

Monthly comparisons may also be affected by missing readings, and October 2026 contains only a partial month.

# How to run it

**Requirements**

- Python 3
- Python packages: `requests` and `duckdb`
- Internet connection for collecting new LAQN data

**1. Clone the repository and open the project folder**

```bash
git clone <repository-url>
cd PropLens
```

Replace `<repository-url>` with the GitHub repository URL.

**2. Create a virtual environment**

On Windows PowerShell:

```powershell
python -m venv .venv
```

**3. Install dependencies**

```powershell
.\.venv\Scripts\python.exe -m pip install requests duckdb
```

**4. Configure data collection**

Open `SRC/config.py` to review the selected monitoring stations, pollutants, historical start date and request limits.

**5. Run the data pipeline**

```powershell
.\.venv\Scripts\python.exe SRC/pipeline.py
```

This runs the data collection and loading scripts.

Existing cached daily JSON files are reused rather than downloaded again. Previously processed files are also tracked in the database.

**6. Run the building analyses**

```powershell
.\.venv\Scripts\python.exe SRC/match_properties.py
.\.venv\Scripts\python.exe SRC/compare_properties.py
.\.venv\Scripts\python.exe SRC/monthly_trends.py
```

The matching script creates or updates `Data/property_matches.csv`.

The two analysis scripts produce CSV reports in the `Outputs` folder.

**7. Optional data-quality checks**

```powershell
.\.venv\Scripts\python.exe SRC/check_database.py
.\.venv\Scripts\python.exe SRC/check_data_quality.py
```

Run commands from the project's main directory so the relative file paths resolve correctly.

**Note:** The repository's final dependency list and setup instructions will be checked before submission.

# What I would do next

Given more development time, I would:

1. **Improve monitoring station selection.** Assess nearby stations using distance, station type, historical availability and similarities between the monitoring environment and the building surroundings.

2. **Expand the particulate matter analysis.** Include PM₂.₅ comparisons alongside NO₂ where suitable historical measurements are available.

3. **Strengthen data-quality checks.** Detect entirely missing timestamps and investigate longer periods of incomplete measurements, rather than checking only records already stored.

4. **Improve resilience to API failures.** Introduce more targeted error handling, retries and tests for unexpected API responses.

5. **Improve interpretation for different populations.** Provide additional context about why air quality is relevant to users of schools, hospitals, care homes and other buildings, without claiming to measure individual exposure or health outcomes.

6. **Develop a clearer visual interface.** Display comparisons, monitoring-station locations and historical trends through a dashboard.

# Where AI helped

I used ChatGPT as a learning and development assistant while building PropLens.

AI helped me:

- Understand Python concepts, DuckDB SQL and the structure of an ETL pipeline.
- Break the project into manageable development stages.
- Draft and explain code, including comments describing what each section does.
- Troubleshoot errors involving file paths, variable definitions and code organisation.
- Discuss data engineering choices such as caching, duplicate prevention, monitoring-station selection and data-quality warnings.
- Improve the clarity of project documentation and reporting.

I used the explanations to develop my understanding of the code and tested the scripts locally using real LAQN API responses.

I also changed the project's direction during development, moving from a commercial-property comparison to exploring air quality in relation to the populations using different buildings.

**AI was used as a support tool, not as a substitute for testing or understanding the implementation.**