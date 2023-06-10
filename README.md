
# Route Planning and Scheduling

This repository contains python implementation of a novel VRP-based Route Planner with multiple resource and time-window constraints.
## How to use
### METHOD 1
1. Install Anaconda, VS Code -
```
https://www.anaconda.com/download
https://visualstudio.microsoft.com/downloads/
```
2. Open VS Code and install required libraries environment using conda 
```
conda env create -f env39.yml
conda activate env39
```
3. Now inside VS Code go to src directory and run main.py, passing a csv input file as an argument
```
python main.py ../data/processed_10.csv
```

### METHOD 2
1. Create a Google Sheets App and make a 'Input' sheet and 'VRP Settings' with appropriate data schema.
2. Create a Google Cloud function with the files in 'gcp-function'
3. Now run the Extension/Macro named 'VRP' in Google Sheets.
Thanks! :)
