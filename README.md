# Internet of Things and Cybersecurity
## 	Lab 2 - Internet of Things and Raspberry - University of South Eastern Norway

# Raspberry
To run this project, make sure to make the following connections:
**TODO** Add image
Rename the file `.env.example` to `.env` and fill in the required service identifiers. Also make sur to install the required dependencies:
```bash
cp .env.example .env # Copy the example config file
pip3 install -r requirements.txt  # Install dependencies
```
Then execute the python script on the Raspberry Pi
```bash
python3 main.py
```

# Data analysis
To run the data analysis, make sure to have the following dependencies installed and the `.env` file filled out.
```bash
cp .env.example .env # Copy the example config file
pip3 install -r requirements.txt  # Install dependencies
```
Then execute one of the python script on your computer
For real time data analysis:
```bash
python3 data_analysis_mqtt.py
```
For database data analysis:
```bash
python3 data_analysis_mongodb.py
```