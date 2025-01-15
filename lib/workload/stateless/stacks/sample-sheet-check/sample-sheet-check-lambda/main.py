import json
import logging
import os
import argparse

from src.checker import construct_sample_sheet, run_sample_sheet_content_check, run_sample_sheet_check_with_metadata
from src.logger import set_logger
from src.v2_samplesheet_builder import v1_to_v2_samplesheet

def get_argument():
    parser = argparse.ArgumentParser(
        description="Run sample sheet check locally."
    )
    parser.add_argument(
        "--path",
        required=True,
        help="The path to the sample sheet file.",
    )

    parser.add_argument(
        "--log-path",
        default="log/ss-checker.log",
        help="Name of the output file for the sscheck log file. Default: log/ss-checker.log",
    )

    parser.add_argument(
        "--skip-metadata-check", action="store_true", default=False,
        help="Skip sample sheet check against metadata API (API token required)."
    )

    parser.add_argument(
        "--skip-v2", "--skip-v2-sample sheet-output", action="store_true", default=False,
        help="Skip generating the sample sheet v2. ('--skip-metadata-check' must be set to False)."
    )

    parser.add_argument(
        "--v2-filename",
        default="SampleSheet_v2.csv",
        help="Name of the output file for the generated sample sheet v2. Default: SampleSheet_v2.csv",
    )

    args_input = parser.parse_args()

    print("#" * 30)
    print(f"Sample sheet (SS) Path    : {args_input.path}")
    print(f"Log path                  : {args_input.log_path}")
    print(f"Skip SS Check w/ metadata : {args_input.skip_metadata_check}")
    print(f"Skip generating v2        : {True if args_input.skip_metadata_check is True else args_input.skip_v2}")
    print(f"SS V2 output (if enabled) : {args_input.v2_filename}")
    print("#" * 30)

    return args_input


if __name__ == "__main__":
    args = get_argument()
    filepath = args.path
    log_path = args.log_path
    v2_filename = args.v2_filename
    result = {
        "Check status": "PASS", "Log path": log_path, "V2 SampleSheet (if enabled)": v2_filename
    }

    # Setup logger logistic
    directory = os.path.dirname(log_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    set_logger(log_path=log_path, log_level=logging.INFO)

    # Construct and run sample sheet checker
    sample_sheet = construct_sample_sheet(filepath)
    run_sample_sheet_content_check(sample_sheet)

    if not args.skip_metadata_check:

        token = os.environ.get("JWT_AUTH", None)
        if token is None:
            raise ValueError("JWT_AUTH environment variable is not set.")

        run_sample_sheet_check_with_metadata(sample_sheet, token)

    result = {"Check status": "PASS", "Log path": log_path}

    if not args.skip_v2 and not args.skip_metadata_check:
        try:

            v2_sample_sheet_str = v1_to_v2_samplesheet(sample_sheet)

            with open(v2_filename, 'w') as file:
                file.write(v2_sample_sheet_str)
        except Exception as e:
            logging.error(f"Error generating v2 sample sheet: {e}")
            raise e

        result["V2 SampleSheet (if enabled)"] = v2_filename

    print("\n")
    print(json.dumps(result, indent=4))
