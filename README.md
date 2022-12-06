# cardaviz
CardaviZ has a mission to provide the community with compelling visualizations to help them gain insights into the Cardano ecosystem.

iT is a framework for visualizing Cardano blockchain data.  It is built on top of cardano-db-sync, but can incorporate data from other sources.  The initial implementation currently provides a visualization of stake pool performance.

## Technical Implementation
The application consists of a Flask app that serves HTML from templates, a Javascript library built on top of Paper.js and a Python script that pulls data from cardano-db-sync database, processes it for quick rendering in the UI and saves the processed data to json files that can be quickly served by a Flask route.

## Getting Started
The framework is designed for quick and easy experimentation.  It contains processed json files for each active Cardano stake pool in the data folder so that someone can clone this repository and start experimenting with rendering the data and ranking the stake pools in different ways without the complexity and overhead of running cardano-node, cardano-db-sync and a Postgresql database.  Of course, these components are needed to keep the data automatically up to date with the blockchain, but not needed for anyone wanting to experiment with historical data.

## Running the visualizations 
To run just the visualizations without data updating, run the following:
```
pip install virtualenv
python -m venv venv
pip install -r requirements.txt
source venv/bin/activate
```
or on Windows, replace the last line with 
```commandline
venv\Scripts\activate.bat
```
And then run flask with:
```commandline
flask --app main run
```
After that, you should be able to load up this URL in a browser 
http://127.0.0.1:5000/pools/spkl
and see a performance visualization of the SPKL stake pool.

>Note:  this runs a development Flask server. Using it in a production environment would have severe security and perormance consequences.  Read up on how to run a production Flask server before exposing it to the world.

## Running data updates
To run the data updates, you will need a postgresql database that is being updated with cardano-db-sync.  Open database.ini and fill in the information to connect to your database.

Then run the following to start updating the json files in the data folder continuously:
```commandline
python update.py
```
When you first run it, it might take a few minutes to a few hours depending on far behind the data in your data directory is.  Once it's caught up, it will only update as new blocks are inserted into the database. The updated data will be visible in the visualisations on the next refresh of your browser.
