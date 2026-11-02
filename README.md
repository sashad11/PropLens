
# What I built and who for

# PropLens | Exploring London's air through the spaces we use

Air quality is something that affects all of us, but it isn't necessarily something we think about in our everyday lives.

We spend so much of our time studying, working, receiving medical care or simply being at home. I've always been interested in people and the environments that shape our experiences, so I wanted to explore how data could help us understand something that often goes unnoticed.

That curiosity became **PropLens**.

PropLens is my data engineering project exploring historical air pollution measurements from monitoring stations near six different types of buildings in London.

I chose these buildings because the people using them have different needs and circumstances. For example, a primary school raises questions about children's developing lungs, while a hospital or care home brings the needs of potentially more vulnerable people into consideration.

I wasn't trying to determine whether a particular building is safe or unsafe. I wanted to understand what environmental data could tell us, how reliable that data is, and how to present it responsibly.

### The six locations

| Building | Type |
|---|---|
| Fox Primary School | School |
| St Thomas' Hospital | Hospital |
| Magnolia Court Care Home | Care home |
| UCL North West Wing | University |
| 80 Strand | Office |
| Barbican Estate | Residential |

PropLens uses Python, DuckDB and SQL to collect, store, validate and analyse air pollution measurements. I also built a Streamlit dashboard to make the results easier to explore.

**An important distinction:** PropLens does not measure pollution inside these buildings or estimate anyone's personal exposure. It uses measurements from nearby monitoring stations to provide historical environmental context.

This is an exploratory educational project, not a health risk assessment.

# The data

## Where the data comes from

I used the **London Air Quality Network (LAQN)** API, provided by the Environmental Research Group at Imperial College London.

API documentation:

https://api.erg.ic.ac.uk/AirQuality/help

I focused on two pollutants:

* **Nitrogen dioxide (NO2):** A pollutant associated with combustion, particularly road traffic, and with respiratory health effects.
* **Fine particulate matter (PM2.5):** Very small airborne particles associated with respiratory and cardiovascular health effects.

Both are measured in micrograms per cubic metre.

The main historical analysis covers **1 August to 28 October 2026**, a period of 89 days.

I also use LAQN station metadata, including station names, coordinates, monitoring environments and available pollutants.

Alongside this, I created `Data/properties.csv`, containing the names, building types and approximate coordinates of my six chosen locations.

## Different forms of data in the project

I deliberately kept different stages of the data separate.

| Data | Purpose |
|---|---|
| Raw JSON files | Preserve the original API responses |
| Building CSV | Stores the six locations and their coordinates |
| Station metadata | Provides monitoring station information |
| DuckDB database | Stores structured hourly measurements |
| Output CSV reports | Stores the results of the analysis |
| Streamlit dashboard | Displays the findings visually |

Keeping the raw JSON files was particularly important to me.

As I learned more about data engineering, I realised that collecting data successfully once wasn't enough. I wanted to be able to rebuild my database, understand where a reading came from and investigate problems without always requesting the same historical data again.

The local DuckDB database is not included in GitHub because it can be recreated from the saved raw data.

**Data attribution:** Air quality measurements and station information come from LAQN. PropLens is an independent educational project and is not affiliated with LAQN.

# How it works

PropLens follows an Extract, Transform and Load (ETL) approach.

I originally thought of the project as collecting data and producing some comparisons. As I developed it, I realised that a large part of data engineering involves making sure those steps can be repeated reliably, especially when data is missing, corrected or unexpectedly formatted.

The pipeline therefore does more than simply download pollution readings.

## 1. Collecting data from the API

Python requests hourly measurements from the LAQN API.

The collector saves the downloaded responses as JSON files in `Data/Raw/`.

Saving the raw responses allows me to trace measurements back to their source and rebuild the database without downloading the full historical dataset again.

The collection process also includes:

* Validation of API responses before accepting the data.
* Retry logic for temporary API failures.
* Clear reporting when requests fail.
* Local caching to avoid unnecessary repeated downloads.
* A configurable refresh period for recent observations.

### Handling API failures

One challenge I considered was what would happen if an API request timed out or returned an unexpected response.

The collector retries temporary failures up to three times.

If the request still fails, the script reports the problem rather than silently treating it as a successful download.

I added automated tests to check this behaviour, including a test that simulates temporary timeouts.

## 2. Handling corrected measurements

This was an important improvement I made after receiving feedback on my project.

Initially, I focused on avoiding duplicate downloads and duplicate database records.

However, I realised that an existing measurement might later be corrected by LAQN. Simply skipping files that had already been downloaded could mean missing those corrections.

To address this, I added a configurable seven day refresh window.

The collector requests recent completed days again, even when a cached file already exists.

I also introduced **SHA256 file hashing**.

SHA256 creates a digital fingerprint of a file. The loader compares this fingerprint with the one previously stored in DuckDB.

If the file has changed, the loader processes it again and checks whether the actual measurements have changed.

This is an important distinction because a changed JSON file does not necessarily mean a pollution reading has changed.

### Updating existing records

The `measurements` table uses a composite primary key consisting of:

* Station code
* Pollutant code
* Measurement timestamp

Together, these identify a unique hourly measurement.

If a measurement already exists, the loader can update its value using SQL conflict handling rather than inserting a duplicate.

I tested the revised process and it successfully detected and updated one previously recorded measurement.

I found this particularly satisfying because it demonstrated why the additional logic was useful in practice.

The seven day refresh period is a practical project choice. It does not guarantee that corrections to older historical readings will always be detected.

## 3. Storing data in DuckDB

I chose DuckDB because I wanted a structured way to store and analyse the measurements using SQL.

The main tables are:

| Table | Purpose |
|---|---|
| `measurements` | Stores hourly pollution observations |
| `processed_files` | Tracks processed JSON files and their fingerprints |

DuckDB allows me to query the data, calculate aggregates and enforce uniqueness using a primary key.

I also kept the raw JSON files separate from the database so I could recreate the structured data if needed.

I tested rebuilding the database from the saved raw files and confirmed that the rebuilt version contained the same measurement counts as my working database.

The database has also been tested to ensure that rerunning the loader does not create duplicate measurements.

## 4. Checking data quality

One of the biggest things I learned was that having an hourly record doesn't necessarily mean having a valid pollution measurement.

A station might have a record for every expected hour, but some records can contain missing numerical values.

I preserve missing measurements as SQL `NULL` values rather than replacing them with zero.

A genuine zero reading and a missing reading do not mean the same thing.

PropLens examines data completeness by comparing recorded hours with valid numerical readings.

For the main 89 day historical period, I found that the analysed station and pollutant combinations had all expected hourly timestamps, but some still had significant numbers of missing values.

I created simple project defined completeness labels.

| Valid readings | Label |
|---|---|
| 95% or above | GOOD |
| 80% to below 95% | CAUTION |
| Below 80% | POOR |

These are my own indicators, not official LAQN quality ratings.

I chose not to estimate missing readings through interpolation because I wanted the analysis to remain based on actual recorded measurements.

SQL averages ignore NULL values, but missing readings can still influence how representative an average is, especially if missingness follows a pattern.

This is one reason I wanted data completeness to be visible in the reports.

## 5. Matching buildings to monitoring stations

Each building has approximate latitude and longitude coordinates.

I use the Haversine formula to calculate straight line distances between buildings and monitoring stations.

Initially, I selected stations manually while exploring the available data.

However, I realised that choosing a station simply because it was the closest could create problems.

A nearby station might have poor historical coverage, while a slightly more distant station might have much more complete measurements.

I therefore introduced automatic matching.

For each building and pollutant, PropLens:

1. Identifies monitoring stations with available historical measurements.
2. Checks the percentage of valid readings.
3. Keeps stations meeting the minimum 90% completeness requirement.
4. Selects the nearest eligible station.
5. Reports the distance and monitoring environment.

I also introduced distance labels.

| Distance | Label |
|---|---|
| Up to 2 km | NEARBY |
| More than 2 km and up to 3 km | CAUTION |
| More than 3 km | DISTANT |

These are practical project indicators, not scientifically validated exposure thresholds.

This approach involves a tradeoff.

Prioritising data completeness can mean choosing a more distant station. Magnolia Court Care Home, for example, has monitoring station matches around 4 km away.

I don't consider those measurements a reliable estimate of the exact pollution at the care home. They provide a reference to available monitoring data in the wider area.

Station type also matters. A roadside station and an urban background station may record different pollution levels even if they are geographically close.

I include those details so people can judge the comparisons more carefully.

## 6. Analysing the measurements

I use SQL and Python to produce several analytical reports.

These cover:

* Average NO2 concentrations associated with each building's selected station.
* Average PM2.5 concentrations associated with each building's selected station.
* Monthly pollution trends.
* Hourly pollution patterns.
* Weekday and weekend comparisons.
* Monitoring station completeness.
* Building and station matching information.

### Main output files

| File | Contents |
|---|---|
| `Outputs/station_quality.csv` | Historical data completeness by station and pollutant |
| `Outputs/station_matches.csv` | Automatic building and station matches |
| `Outputs/property_comparison.csv` | Building comparisons for NO2 |
| `Outputs/pm25_comparison.csv` | Building comparisons for PM2.5 |
| `Outputs/monthly_trends.csv` | Monthly NO2 averages |
| `Outputs/monthly_pm25.csv` | Monthly PM2.5 averages |
| `Outputs/hourly_patterns.csv` | Hourly weekday and weekend averages |

One issue I was especially careful about was avoiding misleading comparisons.

Several buildings share the same monitoring station.

For example, multiple buildings are matched to CE3, meaning they use the same underlying pollution observations.

Those should not be treated as independent measurements simply because they appear beside different building names.

The dashboard therefore displays each monitoring station only once in the station comparison charts.

## 7. Streamlit dashboard

After building the data pipeline and analysis, I wanted a way to make the results more accessible.

I used Streamlit and Plotly to create an interactive dashboard.

The dashboard includes:

* A choice between NO2 and PM2.5.
* Average concentration comparisons by monitoring station.
* A building comparison table.
* Monthly pollution trends.
* Hourly weekday and weekend patterns.
* A map showing building and monitoring station locations.

The dashboard reads the prepared CSV reports rather than repeating the main data processing.

I chose this approach because I wanted to keep the engineering and analysis separate from the visual presentation.

The dashboard runs locally. It is not currently hosted as a public website.

Some visual components, including the map background, require an internet connection.

### Interpretation and limitations

I think it's particularly important to be honest about what the results do and do not show.

PropLens:

* Uses historical monitoring station measurements, not sensors inside buildings.
* Does not measure personal exposure or health risk.
* Sometimes assigns multiple buildings to the same station.
* May use stations several kilometres from a building.
* Uses straight line distance rather than a detailed pollution dispersion model.
* Cannot establish why a particular pollution pattern occurs.
* Uses a fixed historical analysis period ending on 28 October 2026.

I see these limitations as an important part of the project rather than something to hide.

## 8. Testing and reproducibility

I added automated tests because I wanted more confidence that changes to my code wouldn't break the pipeline.

The current test suite contains nine tests covering:

* API response validation.
* Handling missing measurements.
* Handling unexpected station data.
* Retry behaviour after temporary failures.
* Preventing duplicate database measurements.
* Updating corrected measurements.
* Geographic distance calculations.

I also tested rebuilding the database from saved JSON files and confirmed that the rebuilt measurements matched the working database.

The tests don't cover every possible failure, but they've helped me move beyond relying entirely on manual checks.

### Project diagrams

I've included two diagrams to make the project easier to understand.

[View the data pipeline](docs/pipeline.md)

[View the DuckDB data model](docs/data_model.md)

# How to run it

I developed PropLens using Python, SQL, DuckDB and Visual Studio Code on Windows.

## Requirements

* Python 3
* Git
* The packages listed in `requirements.txt`
* An internet connection for collecting data from LAQN

## 1. Clone the repository

```bash
git clone https://github.com/sashad11/PropLens.git
cd PropLens
```

## 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
```

## 3. Install the required packages

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. Review the configuration

Open `SRC/config.py` to review the configured collection settings, including the stations, pollutants and refresh period.

## 5. Collect and load data

To run the main pipeline:

```powershell
.\.venv\Scripts\python.exe SRC/pipeline.py
```

The project also provides separate collection and loading scripts:

```powershell
.\.venv\Scripts\python.exe SRC/collect_new.py
.\.venv\Scripts\python.exe SRC/load.py
```

The saved raw JSON files can be used to rebuild the local DuckDB database.

## 6. Generate the analysis reports

Run the following commands from the main PropLens directory, in this order:

```powershell
.\.venv\Scripts\python.exe SRC/station_quality.py
.\.venv\Scripts\python.exe SRC/match_stations.py
.\.venv\Scripts\python.exe SRC/compare_properties.py
.\.venv\Scripts\python.exe SRC/compare_pm25.py
.\.venv\Scripts\python.exe SRC/monthly_trends.py
.\.venv\Scripts\python.exe SRC/monthly_pm25.py
.\.venv\Scripts\python.exe SRC/hourly_patterns.py
```

The analysis results are written into the `Outputs` directory.

## 7. Run the dashboard

After generating the reports, start Streamlit:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

Streamlit displays a local URL in the terminal, usually:

`http://localhost:8501`

Open that address in your browser to explore the dashboard.

Keep the terminal running while using it.

## 8. Run the automated tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The test suite currently contains nine tests.

## 9. Optional database checks

```powershell
.\.venv\Scripts\python.exe SRC/check_database.py
.\.venv\Scripts\python.exe SRC/check_data_quality.py
.\.venv\Scripts\python.exe SRC/check_missing_hours.py
```

Run all commands from the main PropLens directory so the relative file paths resolve correctly.

# What I would do next

I'm proud of how much this project has developed, but there are several things I would explore if I had more time.

## 1. Improve station representativeness

My biggest priority would be improving how PropLens chooses monitoring stations.

Distance and data completeness are useful starting points, but they don't fully describe the environment around a building.

I'd like to investigate road proximity, monitoring environments, surrounding land use and other factors that could make one station more suitable than another.

I'd also explore what to do when there isn't a sufficiently representative station nearby, rather than always producing a numerical comparison.

## 2. Expand the historical dataset

The current analysis uses almost three months of measurements.

I'd like to extend this to a full year so I could investigate longer term and seasonal patterns.

That could also help me understand whether the trends in my current results are typical or specific to the period I selected.

## 3. Investigate missing data more deeply

I currently measure completeness and preserve missing values.

A useful next step would be studying when those gaps occur.

For example, I'd like to know whether missing readings are concentrated at certain stations, times of day or periods of unusual pollution.

I'd also investigate whether any patterns of missingness could bias the averages.

## 4. Improve automation and testing

I'd like to add more integration tests covering the complete journey from collecting a JSON response to updating the database and regenerating the reports.

I'd also consider making the reporting period configurable, so the dashboard could easily display newer analysis windows.

For a larger project, I'd explore automated scheduling and monitoring rather than relying on manually running scripts.

## 5. Develop the dashboard further

I'd like to improve the map with clearer station information and more detailed explanations of the matching decisions.

Eventually, I could explore hosting PropLens so people could access it without running Python locally.

However, I wanted to prioritise making the underlying pipeline reliable and understandable before expanding the interface.

# Where AI helped

I used AI throughout this project as a learning and development assistant.

I want to be transparent about that because I'm still developing my programming skills, and a large part of this project has involved learning concepts that were completely new to me.

At the beginning, I had an idea and a genuine interest in the problem, but I didn't always know how to translate that idea into working Python and SQL.

AI helped me break complicated tasks into smaller steps, understand unfamiliar syntax and troubleshoot errors.

I used it to help with:

* Understanding Python, SQL and ETL concepts.
* Planning the structure of the pipeline.
* Exploring different approaches to caching and database loading.
* Writing and explaining code.
* Debugging errors, particularly when scripts didn't behave as expected.
* Understanding data completeness, duplicate prevention and corrected measurements.
* Exploring how to test the pipeline.
* Improving the structure and clarity of my documentation.

I also used AI to discuss the limitations of the analysis and challenge my assumptions about how monitoring stations should be matched to buildings.

### What I found challenging

One of my biggest challenges was understanding how the individual parts of the project connected.

I could often understand a small piece of code once it was explained, but understanding why that piece belonged in the wider pipeline took more practice.

I also found debugging difficult at times, especially when errors came from indentation, unfamiliar syntax or assumptions about the structure of the API response.

Rather than simply moving past those errors, I tried to understand what caused them and what I could do differently next time.

Receiving feedback also changed how I thought about the project.

For example, I initially focused on preventing duplicate measurements, but feedback made me realise that preventing duplicates wasn't enough if the source data could later be corrected.

That led me to add the refresh window, file hashes and update logic.

I tested the code locally, checked the outputs and made decisions about the direction and scope of the project.

### How the project changed

PropLens originally started as an idea connected to commercial property and investment.

As I explored the data, I found myself becoming more interested in the people using different spaces and the environmental conditions surrounding those places.

That shift shaped the six building types I selected and the way I chose to present the results.

### What I've learned

This project has taught me more than how to collect data from an API.

I've learned why reproducibility matters, how small decisions can influence the reliability of an analysis, and why it's important to question what a dataset can actually tell us.

I've also realised that I enjoy the problem solving side of data engineering, even when it takes several attempts to understand or fix something.

There are still plenty of concepts I want to learn, but building PropLens has given me a much clearer understanding of how a data pipeline comes together and made me more confident about continuing to develop my technical skills.
