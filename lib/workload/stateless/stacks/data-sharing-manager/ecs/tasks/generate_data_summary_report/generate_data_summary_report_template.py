#!/usr/bin/env python3

"""
Big script using snakemd to generate an RMarkdown template for a data summary report.

We then run the RMarkdown file to generate the report.

"""
from data_summary_reporting_tools.markdown_helpers import generate_data_summary_report_template
from os import environ
from subprocess import run

def main():
    generate_data_summary_report_template(environ['JOB_ID'])
    render_proc = run(
        [
            "Rscript",
            "-e",
            "rmarkdown::render('data_summary_report.Rmd', output_file = 'data_summary_report.html')"
        ],
        capture_output=True
    )

    if render_proc.returncode != 0:
        print("Error in rendering RMarkdown file")
        print(render_proc.stderr.decode())
        raise Exception("Error in rendering RMarkdown file")


if __name__ == "__main__":
     main()


# ## Archived data test
# if __name__ == "__main__":
#    import subprocess
#    environ['AWS_PROFILE'] = 'umccr-production'
#    environ['AWS_REGION'] = 'ap-southeast-2'
#    environ['DYNAMODB_TABLE_NAME'] = "data-sharing-packaging-lookup-table"
#    environ['DYNAMODB_INDEX_NAME'] = 'context-index'
#    environ['PACKAGE_NAME'] = "package-name"
#    environ['JOB_ID'] = 'pkg.01JR21MF5BFS1M6R3373TR4JRV'
#    environ['OUTPUT_URI'] = 's3://data-sharing-artifacts-843407916570-ap-southeast-2/packages/year=2025/month=03/day=25/pkg.01JQ6ERY7YA9QJAHXN6KCX1RHP/final/SummaryReport.package-name.html'
#    generate_data_summary_report_template(environ['JOB_ID'])
#
#    subprocess.run("Rscript -e \"rmarkdown::render('data_summary_report.Rmd', output_file = 'data_summary_report.html')\"", shell=True)


# if __name__ == "__main__":
#     import subprocess
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['DYNAMODB_TABLE_NAME'] = "data-sharing-packaging-lookup-table"
#     environ['DYNAMODB_INDEX_NAME'] = 'context-index'
#     environ['PACKAGE_NAME'] = "L2401546-test"
#     environ['JOB_ID'] = 'pkg.01JQAWP4W0G3G85X4WGQBZ9VGR'
#     environ['OUTPUT_URI'] = 's3://data-sharing-artifacts-843407916570-ap-southeast-2/packages/year=2025/month=03/day=27/pkg.01JQAWP4W0G3G85X4WGQBZ9VGR/final/SummaryReport.L2401546-test.html'
#     generate_data_summary_report_template(environ['JOB_ID'])
#
#     subprocess.run(
#         "Rscript -e \"rmarkdown::render('data_summary_report.Rmd', output_file = 'data_summary_report.html')\"",
#         shell=True)


## Multiple projects over a run
# if __name__ == "__main__":
#     import subprocess
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['DYNAMODB_TABLE_NAME'] = "data-sharing-packaging-lookup-table"
#     environ['DYNAMODB_INDEX_NAME'] = 'context-index'
#     environ['PACKAGE_NAME'] = "Run-241024_A00130_0336_BHW7MVDSXC-all-data"
#     environ['JOB_ID'] = 'pkg.01JQMY3J4KDJVMHP19DKQTBNKJ'
#     environ['OUTPUT_URI'] = 's3://data-sharing-artifacts-843407916570-ap-southeast-2/packages/year=2025/month=03/day=31/pkg.01JQMY3J4KDJVMHP19DKQTBNKJ/final/SummaryReport.Run-241024_A00130_0336_BHW7MVDSXC-all-data.html'
#     generate_data_summary_report_template(environ['JOB_ID'])
#
#     subprocess.run(
#         "Rscript -e \"rmarkdown::render('data_summary_report.Rmd', output_file = 'data_summary_report.html')\"",
#         shell=True
#     )


## Single project over run example
# if __name__ == "__main__":
#     import subprocess
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['DYNAMODB_TABLE_NAME'] = "data-sharing-packaging-lookup-table"
#     environ['DYNAMODB_INDEX_NAME'] = 'context-index'
#     environ['PACKAGE_NAME'] = "Run-241024_A00130_0336_BHW7MVDSXC-all-data"
#     environ['JOB_ID'] = 'pkg.01JQQ6ZFD9PSNX438ZEP9N6JV3'
#     environ['OUTPUT_URI'] = 's3://data-sharing-artifacts-843407916570-ap-southeast-2/packages/year=2025/month=03/day=31/pkg.01JQMY3J4KDJVMHP19DKQTBNKJ/final/SummaryReport.Run-241024_A00130_0336_BHW7MVDSXC-all-data.html'
#     generate_data_summary_report_template(environ['JOB_ID'])
#
#     subprocess.run(
#         "Rscript -e \"rmarkdown::render('data_summary_report.Rmd', output_file = 'data_summary_report.html')\"",
#         shell=True
#     )


# ## Archived secondary data test
# if __name__ == "__main__":
#     import subprocess
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['PACKAGE_NAME'] = "SBJ04470-umccrise"
#     environ['JOB_ID'] = 'pkg.01JRGZQCZ94HZ82TR0SHKYCG3A'
#     generate_data_summary_report_template(environ['JOB_ID'])
#
#     subprocess.run(
#         "Rscript -e \"rmarkdown::render('data_summary_report.Rmd', output_file = 'data_summary_report.html')\"",
#         shell=True
#     )
