# 01 Advanced basics homework

## Setup

1. Make sure Python 3.11+ is installed 
2. Clone project repository 

```bash
git clone https://github.com/akoval77/01_advanced_basics.git
```

## Run log analyzer with default config

1. Go to project directory and create subdirectory for logs

```bash
cd 01_advanced_basics
mkdir logs
```

2. Copy log files to /logs subdirectory
3. Run log analyzer

```bash
python log_analyzer.py
```
4. Reports will be created in /reports subdirectory

## Run log analyzer with custom configuration
1. Modify parameters in default config.ini file in project directory or create new file with following content
```
[config]
REPORT_SIZE=1000
REPORT_DIR=./reports
LOG_DIR=./log
ERROR_LIMIT=0.5
[logging]
level=DEBUG
filename=log_analyzer.log
```

2. Run log analyzer with --config parameter


```bash
python log_analyzer.py --config ~/my_config.ini
```

## Run unit tests
1. Go to project directory

```bash
cd 01_advanced_basics
```

2. Run tests with following command

```bash
python test_log_analyzer.py 
```
to get verbose output use -v option
```bash
python test_log_analyzer.py -v 
```

## Optional tasks

1. Run poker script with following command

```bash
python poker.py
```
