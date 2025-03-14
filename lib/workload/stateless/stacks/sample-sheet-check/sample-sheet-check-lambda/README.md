# Sample Sheet Checker

## Setup

### Using Python Environment

```shell
conda create -n orcabus_sscheck python=3.12
conda activate orcabus_sscheck
```

### Running Locally

To run the script and see the available options, use the following command:

```shell
python main.py -h

usage: main.py [-h] --path PATH [--log-path LOG_PATH] [--skip-metadata-check] [--skip-v2] [--v2-filename V2_FILENAME]

Run sample sheet check locally.

options:
  -h, --help            show this help message and exit
  --path PATH           The path to the sample sheet file.
  --log-path LOG_PATH   Name of the output file for the sscheck log file. Default: log/ss-checker.log
  --skip-metadata-check
                        Skip sample sheet check against metadata API (API token required).
  --skip-v2, --skip-v2-sample sheet-output
                        Skip generating the sample sheet v2. ('--skip-metadata-check' must be set to False).
  --v2-filename V2_FILENAME
                        Name of the output file for the generated sample sheet v2. Default: SampleSheet_v2.csv

```

Set Environment Variable

```shell
export JWT_AUTH={JWT_TOKEN_HERE}
export METADATA_DOMAIN_NAME=metadata.dev.umccr.org
```

Running example

```shell
 python main.py --path ./tests/sample/sample-1.csv
```
