
# VRP Project for Blinds Installation Company

This repository contains the code and documentation for a Vehicle Routing Problem (VRP) solution that was built for a blinds installation company in Australia. The client was having difficulties manually allocating, scheduling, and managing the routes of all its installers/employees. This project automated and optimized the Constrained Vehicle Routing Problem with Time Windows (CVRP-TW) to help reduce processing time and increase efficiency .

## About the Project
The main goal of this project was to automate and optimize the scheduling and route management for a blinds installation company in Australia. The company was having trouble manually managing the routes and schedules of all its installers/employees, which was leading to inefficiencies and increased processing time. This project is a tool that uses the concept of Constrained Vehicle Routing Problem with Time Windows (CVRP-TW) to solve the client's problem

## Getting Started
To get a local copy up and running follow these simple steps.

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
3. Now reate and run the Extension/Macro  named 'VRP' in Google Sheets.

## Contributing
Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated. If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! 
Thanks! :)

## Screenshots
![routes-output](https://github.com/bhavyaverma1/AndrewVRP/assets/39443863/d86cabdf-0cde-40cc-bba7-818293fc9df7)
![routes-map](https://github.com/bhavyaverma1/AndrewVRP/assets/39443863/aaa5e7ed-03d0-4401-8646-4b5e61499fc8)


## License
This project is licensed under the MIT license. For more information refer to the LICENSE.txt file.
