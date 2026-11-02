
# What I built and who for

## PropLens | Exploring London's air through the spaces we use

Most of us spend our days moving between buildings without giving much thought to the air around them. I wanted to look at that more closely. I've always been interested in people and the environments we spend time in, and I was curious about what pollution data could actually tell us.

PropLens began as an idea about commercial property and investment. As I explored the data, I became more interested in the people who use different buildings. A school, hospital and care home serve very different groups of people, yet they all sit within the same city and its environment. That change in perspective shaped the project.

I chose six London locations to explore:

| Location | Building type |
| --- | --- |
| Fox Primary School | School |
| St Thomas' Hospital | Hospital |
| Magnolia Court Care Home | Care home |
| UCL North West Wing | University |
| 80 Strand | Office |
| Barbican Estate | Residential |

I built a Python and DuckDB pipeline to collect and analyse historical air quality readings from London monitoring stations. I then made a Streamlit dashboard to help explore the results.

I want to be clear about what PropLens does not do. The readings come from monitoring stations, not from sensors inside these buildings. The project provides context about measurements in the wider area. It cannot tell someone their personal exposure or whether a building is safe.

# The data

My source is the [London Air Quality Network (LAQN)](https://api.erg.ic.ac.uk/AirQuality/help). I use hourly measurements for nitrogen dioxide (NO2) and fine particulate matter (PM2.5), reported in micrograms per cubic metre. I also use LAQN metadata for station names, locations and monitoring environments.

I created `Data/properties.csv` to hold the six building names, types and approximate coordinates. Some coordinates represent a general point for the building rather than its exact entrance.

The analysis starts on 1 August 2026. It no longer has a fixed end date. When I run the update process, PropLens finds the latest completed UTC day with all 24 hourly timestamps recorded for each of the 13 configured station and pollutant combinations.

The latest run extended the reporting period to 1 November 2026, covering 93 days and 2,232 expected hours per combination.

Having a timestamp does not mean there is a valid pollution reading for that hour. I check missing numerical values separately.

I keep the data in different forms for different reasons:

1. `Data/Raw/` contains cached JSON responses from the API, so I can trace readings back to the downloaded files and rebuild the database.
2. `Data/properties.csv` holds the locations I chose to investigate.
3. `Data/proplens.duckdb` is the local database used for SQL queries and analysis. I do not commit this generated database to GitHub.
4. `Outputs/` contains the processed CSV reports used by the dashboard, plus `reporting_period.json` with the dates of the latest analysis.

Air quality data and monitoring station information come from LAQN. PropLens is an independent learning project and is not affiliated with LAQN.

# How it works

I wanted PropLens to be something I could rerun, not just a collection of charts made from one download. That meant thinking about missing readings, failed requests, duplicate records and corrections made by the data provider.

## 1. Collecting and saving the data

Python requests hourly NO2 and PM2.5 measurements from the LAQN API and saves the responses as JSON files.

Keeping those original responses means I can rebuild my local database without downloading the whole historical dataset each time.

The collector validates the responses before saving them. It retries temporary failures up to three times and reports requests that still fail.

It also reuses cached data where appropriate, with a configurable seven day refresh period for recent readings.

## 2. Loading data and handling corrections

A separate Python script loads the JSON measurements into DuckDB.

The `measurements` table identifies a reading using three fields together:

1. Station code
2. Pollutant code
3. Measurement timestamp

That combined primary key helps prevent duplicates when I run the pipeline again.

One piece of feedback changed how I approached this. At first, I was focused on stopping duplicate records. I hadn't fully considered that LAQN might correct a reading after I had already downloaded it.

I added SHA256 hashes to give each JSON file a digital fingerprint.

When a refreshed file has a different fingerprint, the loader processes it again and checks the readings. If a measurement has changed, DuckDB updates the existing record instead of inserting a duplicate.

During testing, this process detected and updated a real corrected reading.

The `processed_files` table records which files have been loaded and their fingerprints.

The seven day refresh is my chosen compromise between checking for corrections and avoiding unnecessary API requests. It will not catch every possible correction to older data.

## 3. Checking data quality

I learned quite quickly that having a record for every hour is not the same as having a valid measurement every hour.

Some LAQN records contain missing numerical values.

I keep those readings as `NULL`, rather than replacing them with zero. I check the number of expected hours, the timestamps actually recorded and the number of valid values.

I also calculate the percentage of valid readings for each station and pollutant.

For easier interpretation, I use my own completeness labels:

| Valid readings | Label |
| --- | --- |
| At least 95% | GOOD |
| At least 80% but below 95% | CAUTION |
| Below 80% | POOR |

These are project labels, not official LAQN ratings.

I haven't filled gaps with estimated values. That keeps the results based on observed readings, although averages can still be affected if missing values follow a pattern.

## 4. Matching buildings to stations

I use the Haversine formula to calculate straight line distances from each building to the monitoring stations.

I started by exploring and choosing stations manually, but I later changed this to an automatic process.

For each building and each pollutant, the matching script looks for stations with at least 90% valid readings across the reporting period.

It then chooses the nearest eligible station and records its distance and monitoring environment.

I flag distances using the following categories:

| Distance | Label |
| --- | --- |
| Up to 2 km | NEARBY |
| Over 2 km and up to 3 km | CAUTION |
| Over 3 km | DISTANT |

These are practical warnings I defined for the project, not scientific thresholds.

This is one of the main limitations of PropLens.

A station with good data coverage may be several kilometres away. Magnolia Court Care Home, for example, has distant matches.

Two locations can also share the same station, meaning they share the same underlying measurements.

I show these details instead of treating the figures as separate measurements taken at each building.

Roadside and urban background stations can also have different conditions, even within the same area.

## 5. Producing the analysis

I use SQL and Python to calculate average concentrations, monthly trends, hourly patterns and differences between weekdays and weekends.

The scripts produce CSV reports in `Outputs/`.

The main reports are:

| File | Contents |
| --- | --- |
| `station_quality.csv` | Data completeness by station and pollutant |
| `station_matches.csv` | Building matches, distance and quality information |
| `property_comparison.csv` | NO2 building comparisons |
| `pm25_comparison.csv` | PM2.5 building comparisons |
| `monthly_trends.csv` | Monthly NO2 averages |
| `monthly_pm25.csv` | Monthly PM2.5 averages |
| `hourly_patterns.csv` | Hourly weekday and weekend averages |
| `reporting_period.json` | Start date, end date and expected hourly coverage |

## 6. Updating the reporting period

I originally used a fixed end date for the analysis.

After feedback about making the project more dynamic, I added `SRC/update_all.py` so I could refresh everything with one command.

It runs the collector, loader, reporting period calculation and analysis scripts in sequence.

The reporting window advances to the latest completed UTC date for which every configured station and pollutant combination has 24 recorded hourly timestamps.

All reports then use the same period.

This is a manual update process, not an automatically scheduled daily service.

The dashboard reads the generated reports and shows the new results when it reruns. It does not call the API itself.

## 7. Dashboard

I built a local Streamlit dashboard using Plotly.

It lets me switch between NO2 and PM2.5, compare monitoring stations, view building matches, examine monthly and hourly trends, and see buildings and stations on a map.

I have tried to keep the interpretation careful.

Shared stations appear only once in station comparison charts, and I show distance warnings rather than suggesting that a station measures conditions at the building itself.

The dashboard is not publicly hosted.

## 8. Tests and project diagrams

I added nine automated tests covering:

1. API response validation
2. Temporary failures and retries
3. Distance calculations
4. Duplicate prevention
5. Corrected measurement updates

I also checked that I could recreate the database from the cached JSON files.

The tests help, but they do not yet cover every stage working together in a fully automated environment.

I included two diagrams to make the structure easier to follow:

[Data pipeline](docs/pipeline.md)

[DuckDB data model](docs/data_model.md)

# How to run it

I developed PropLens on Windows using Python, DuckDB, SQL and VS Code.

You need Python 3, Git and an internet connection to collect new LAQN measurements.

## 1. Download the project

```powershell
git clone https://github.com/sashad11/PropLens.git
cd PropLens
```

## 2. Create a virtual environment

```powershell
python -m venv .venv
```

## 3. Install the Python packages

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. Review the settings

Open `SRC/config.py` to see the selected station and pollutant combinations, the historical starting date and the recent refresh settings.

## 5. Refresh the pipeline and reports

Run this command from the main PropLens folder:

```powershell
.\.venv\Scripts\python.exe SRC/update_all.py
```

This runs data collection, DuckDB loading, reporting period selection and all seven report scripts in order.

It creates `Outputs/reporting_period.json` with the reporting dates.

You can also run the collection and loading scripts individually if you want to inspect those stages.

## 6. Open the dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

Open the local address displayed in the terminal, usually `http://localhost:8501`.

Keep the Streamlit process running while using the dashboard.

## 7. Run the tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Optional checks are available in `SRC/check_database.py`, `SRC/check_data_quality.py` and `SRC/check_missing_hours.py`.

# What I would do next

The first thing I would improve is the station matching.

Distance and completeness help, but I would like to consider road proximity, local surroundings and whether the type of monitoring station suits the building.

I would also prefer to leave a building unmatched when there is no sufficiently representative option.

I would extend the historical period to a full year so I could explore seasonal differences.

I'd also examine when missing readings occur, rather than only how many are missing, to understand whether those gaps could affect my conclusions.

For the engineering side, I'd add more tests covering the complete pipeline and look at scheduling the update command to run daily.

I'd also like to make report publication safer if one stage fails, with clear logs showing the last successful update.

Eventually, I could host the dashboard so other people can use it without running the project on their own computers.

# Where AI helped

I used AI as a learning and coding assistant throughout PropLens, and I want to be open about that.

I came into the project with an idea I cared about, but limited experience building a complete pipeline in Python.

AI helped me plan the stages, draft and explain code, understand SQL, troubleshoot errors and improve the documentation.

I also used it to explore options when I wasn't sure how to handle things like missing readings, duplicate records or API corrections.

I found some parts genuinely difficult.

I struggled with Python indentation and unfamiliar syntax, but also with the bigger picture of how each script connected to the next.

Sometimes I understood a line of code on its own but needed more time to understand why it belonged in the pipeline.

Testing things locally, reading the errors and going back over the logic helped me make progress.

Feedback was another important part of the process.

When the issue of corrected readings came up, I realised that preventing duplicates was only part of the problem.

I went back to the code, added the refresh and update logic, and tested it against the data.

I made a similar change when I revisited the fixed reporting dates.

I don't want to present PropLens as something I built without help, or suggest that I now understand every part of data engineering.

But I did choose the direction of the project, question the results, test changes and keep working on the areas I found difficult.

I've learned a lot about how to build a pipeline that can be rerun and checked, and also about how careful you need to be when turning environmental measurements into something people might use to make decisions.

The part I enjoyed most was seeing my interests in people, the environment and data come together in something practical.

It has made me want to keep learning.
