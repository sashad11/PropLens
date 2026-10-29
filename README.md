# What I built and who for

**PropLens | Exploring London's air through the spaces we use**

Air quality is something that affects all of us, but it's not something we necessarily think about when going about our daily lives. Whether we're studying, working, receiving medical care or simply at home, we're constantly interacting with the environment around us.

That was the thinking behind **PropLens**.

I built PropLens as a data engineering project that collects and analyses London's historical air pollution data, with a particular interest in the different people who use different types of buildings.

For example, air quality around a primary school may be especially relevant when considering children's developing lungs, while a care home or hospital brings different population vulnerabilities into consideration.

I wanted to explore how I could use data to make these environmental considerations more visible and understandable.

For this first version, I've chosen six real London locations:

| Building | Type |
|---|---|
| Fox Primary School | School |
| St Thomas' Hospital | Hospital |
| Magnolia Court Care Home | Care home |
| UCL North-West Wing | University |
| 80 Strand | Office |
| Barbican Estate | Residential |

PropLens uses Python and DuckDB to collect, store and analyse air pollution measurements from monitoring stations near these buildings.

**A note on interpretation:** PropLens is an exploratory tool, not a health-risk assessment. The measurements come from monitoring stations, not from inside the buildings themselves. They provide environmental context rather than a direct measurement of anyone's personal exposure.

# The data

The main data source is the **London Air Quality Network (LAQN)**, accessed through its API:

https://api.erg.ic.ac.uk/AirQuality/help

For this project, I've focused on two pollutants:

- **Nitrogen dioxide (NO₂):** A gas associated with combustion, particularly traffic emissions, which can affect respiratory health.
- **Fine particulate matter (PM₂.₅):** Tiny airborne particles that can reach deep into the lungs and are associated with respiratory and cardiovascular health effects.

Both are measured in micrograms per cubic metre (µg/m³).

My current historical dataset covers **1 August to 28 October 2026**, providing 89 days of hourly measurements from selected LAQN monitoring stations.

I've also used LAQN station metadata, which includes station names, geographical coordinates, monitoring environments and listed pollutants.

Alongside this, I created a small CSV dataset containing the six building locations, their types and approximate coordinates.

The project retains several forms of data:

- **Raw JSON:** Original API responses, kept so I can trace the measurements back to their source.
- **Building and station CSVs:** The locations used in the analysis and their monitoring-station matches.
- **DuckDB database:** Cleaned hourly measurements used for querying and analysis.
- **Output CSVs:** Building comparisons and monthly pollutant trends.

Some building coordinates are approximate reference points rather than exact entrances.

**Data attribution:** Air quality measurements and monitoring-station information are provided by the London Air Quality Network (LAQN). PropLens is an independent educational project and is not affiliated with LAQN. Please refer to LAQN's published guidance and terms when reusing the source data.

# How it works

PropLens follows an **Extract, Transform and Load (ETL)** process.

I wanted to build something that could be run more than once, rather than a script that downloads some data, produces a result and stops there.

**1. Collecting the data**

The collection script requests hourly measurements from the LAQN API for selected monitoring stations and pollutants.

Each daily API response is saved as its original JSON file.

Before making a request, the script checks whether that file has already been downloaded. If it exists, the script reuses the cached version instead of contacting the API again.

I've also included a short delay between requests to avoid unnecessarily overloading the API.

This was one of my first lessons in thinking about a data pipeline beyond simply getting the data successfully.

**2. Loading the data into DuckDB**

The loading script reads the saved JSON files and extracts the station code, pollutant, measurement timestamp and recorded value.

Missing numerical readings are stored as SQL `NULL` values rather than being replaced with zero, because missing data and a genuine zero measurement mean different things.

The measurements are then stored in DuckDB.

To make the pipeline safe to rerun, I introduced:

- A composite primary key to prevent duplicate station–pollutant–timestamp records.
- Conflict handling to avoid inserting duplicates.
- A `processed_files` table to track which raw files have already been loaded.

I tested this by running the pipeline twice. The second run inserted **zero new records**, confirming that rerunning it with unchanged cached data did not duplicate measurements.

**3. Checking data quality**

One thing I quickly realised is that having data doesn't necessarily mean having *usable* data.

Some monitoring stations were listed as active but returned no numerical readings on the dates I tested. Others had substantial gaps.

PropLens therefore calculates the percentage of stored measurements containing valid numerical values.

I've used three simple project-defined labels:

| Completeness | Label |
|---|---|
| 95% or above | GOOD |
| 80% to below 95% | CAUTION |
| Below 80% | POOR |

These aren't official LAQN ratings. They're indicators I introduced to make missing data easier to spot.

An important limitation is that the current calculation checks missing values within stored records; it doesn't fully identify timestamps that are absent altogether.

**4. Matching buildings to monitoring stations**

To connect the air pollution data with my chosen buildings, I used latitude and longitude coordinates and the Haversine formula to calculate approximate straight-line distances.

My initial approach was to select monitoring stations across London and then match properties to them.

However, once I settled on the six building types, I realised that **choosing a station purely because it's nearby isn't necessarily the best approach**.

A nearby station might have missing measurements, or it might be located beside a busy road when the building is in a quieter environment.

So I explored alternative stations, tested their data availability and considered the distance and monitoring environment before deciding which measurements to use.

For transparency, the building reports flag stations using my own provisional distance categories:

- **NEARBY:** Up to 2 km.
- **CAUTION:** Over 2 km and up to 3 km.
- **DISTANT:** Over 3 km.

These are practical project indicators, not scientific exposure thresholds.

**5. Analysing the results**

I used SQL queries in DuckDB to calculate historical averages, measurement completeness and monthly trends.

The main outputs are:

| Output file | What it shows |
|---|---|
| `Outputs/property_comparison.csv` | NO₂ building comparisons, distances and quality warnings |
| `Outputs/monthly_trends.csv` | Monthly NO₂ averages and valid reading counts |
| `Outputs/pm25_comparison.csv` | PM₂.₅ building comparisons for locations with selected station matches |
| `Outputs/monthly_pm25.csv` | Monthly PM₂.₅ trends by monitoring station |

One issue I wanted to be careful about was **avoiding misleading comparisons**.

Several buildings share the same monitoring station. That means they also share the same underlying pollution measurements, even though they're different buildings.

I made sure this is highlighted in the NO₂ report rather than presenting identical measurements as independent observations.

For PM₂.₅, Barbican Estate currently has no confirmed suitable station match, so I've excluded it from the numerical comparison rather than assigning it an arbitrary value.

The analysis also makes no claim about whether individual buildings are safe or unsafe. Understanding the limitations of the data is just as important as calculating the averages.

# How to run it

PropLens was developed using Python, DuckDB and Visual Studio Code.

**Requirements**

- Python 3
- Git
- Python packages listed in `requirements.txt`
- An internet connection when collecting new data from LAQN

**1. Clone the repository**

```bash
git clone https://github.com/sashad11/PropLens.git
cd PropLens
```

**2. Create a virtual environment**

On Windows PowerShell:

```powershell
python -m venv .venv
```

**3. Install the required packages**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**4. Review the collection settings**

Open `SRC/config.py` to see the selected station–pollutant combinations, historical start date and maximum number of new daily downloads per target.

**5. Run the ETL pipeline**

```powershell
.\.venv\Scripts\python.exe SRC/pipeline.py
```

This runs the data collection and loading stages.

Previously downloaded JSON files are reused, and files already recorded as processed are not loaded again.

The local DuckDB database is not included in the repository because it can be recreated from the raw data.

**6. Generate the reports**

```powershell
.\.venv\Scripts\python.exe SRC/match_properties.py
.\.venv\Scripts\python.exe SRC/compare_properties.py
.\.venv\Scripts\python.exe SRC/monthly_trends.py
.\.venv\Scripts\python.exe SRC/compare_pm25.py
.\.venv\Scripts\python.exe SRC/monthly_pm25.py
```

The resulting CSV files are saved in the `Outputs` folder.

**7. Optional database checks**

```powershell
.\.venv\Scripts\python.exe SRC/check_database.py
.\.venv\Scripts\python.exe SRC/check_data_quality.py
```

Run these commands from the main PropLens directory.

# What I would do next

There are several things I'd like to explore if I had more time.

**Improve station matching**

This is probably my biggest priority. I'd like to make station selection more automated, taking into account distance, station type, historical completeness and the surroundings of each building.

I'd also like to investigate alternative buildings or monitoring locations where the current matches are too distant.

**Expand the historical dataset**

The project currently covers almost three months. Extending this to six months or a full year would allow for more meaningful seasonal comparisons and a better understanding of longer-term trends.

**Strengthen missing-data checks**

I'd like to identify entirely missing timestamps, rather than just counting missing values in records that have already been stored.

**Make the pipeline more resilient**

Although the collection and loading process works, I'd like to introduce more targeted tests and better handling of API failures, unexpected responses and temporary network issues.

**Expand the PM₂.₅ analysis**

PM₂.₅ is now included, but there is room to improve geographical coverage and find suitable monitoring stations for all six buildings.

**Build an interactive dashboard**

Eventually, I'd like PropLens to become something people can explore for themselves, with a map of monitoring stations, building locations, pollutant comparisons and historical trends.

For now, I wanted to prioritise getting the underlying data pipeline working properly before adding a more visual interface.

# Where AI helped

I used AI throughout the project as a learning and development assistant.

As someone still building confidence with Python and data engineering, I found it useful for breaking unfamiliar tasks into manageable steps and understanding *why* certain approaches worked.

AI supported me with:

- Understanding Python concepts, SQL queries and ETL design.
- Structuring scripts and adding explanations to make the code easier to follow.
- Troubleshooting errors and understanding their causes.
- Exploring approaches to caching, duplicate prevention and data-quality checks.
- Discussing monitoring-station selection and the limitations of environmental data.
- Improving the clarity of the project documentation.

I tested the code locally, reviewed the outputs and made decisions about how I wanted the project to develop.

For example, PropLens originally started as an idea focused on commercial property investment. As I explored the data and thought more about its potential uses, I became more interested in the people who occupy different spaces and why environmental conditions might matter to them. That change in direction shaped the final project.
