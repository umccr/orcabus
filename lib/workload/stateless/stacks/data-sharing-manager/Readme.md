# Data Sharing Manager

## Description

The data sharing manager is divided into three main components -
1. Package generation
2. Package validation
3. Package sharing

For all three parts, we recommend using the data-sharing-tool provided.

### Installing the Data Sharing Tool

In order to generate a package, we recommend installing the data-sharing-tool by running the following command (from this directory).

Please preface the command with 'bash' 

```bash
bash scripts/install.sh
```

## Package Generation

> This component expects the user to have some familiarity with AWS athena

We use the 'mart' tables to generate the appropriate manifests for package generation.

You may use the UI to generate the manifests, or you can use the command line interface as shown below.  

In the example below, we collect the libraries that are associated with the project 'CUP' and the 
sequencing run date is greater than or equal to '2025-04-01'.

We require only the lims-manifest when collecting fastq data.  

The workflow manifest (along with the lims-manifest) is required when collecting secondary analysis data.

```bash
WORK_GROUP="orcahouse"
DATASOURCE_NAME="orcavault"
DATABASE_NAME="mart"

# Initialise the query
query_execution_id="$( \
  aws athena start-query-execution \
      --no-cli-pager \
      --query-string " \
        SELECT *
        FROM lims 
        WHERE 
          project_id = 'CUP' AND
          sequencing_run_date >= CAST('2025-04-01' AS DATE)
      " \
      --work-group "${WORK_GROUP}" \
      --query-execution-context "Database=${DATABASE_NAME}, Catalog=${DATASOURCE_NAME}" \
      --output json \
      --query 'QueryExecutionId' \
)"

# Wait for the query to complete
while true; do
  query_state="$( \
    aws athena get-query-execution \
      --no-cli-pager \
      --output json \
      --query-execution-id "${query_execution_id}" \
      --query 'QueryExecution.Status.State' \
  )"

  if [[ "${query_state}" == "SUCCEEDED" ]]; then
    break
  elif [[ "${query_state}" == "FAILED" || "${query_state}" == "CANCELLED" ]]; then
    echo "Query failed or was cancelled"
    exit 1
  fi

  sleep 5
done

# Collect the query results
query_results_uri="$( \
  aws athena get-query-execution \
    --no-cli-pager \
    --output json \
    --query-execution-id "${query_execution_id}" \
    --query '.QueryExecution.ResultConfiguration.OutputLocation' \
)"
  
# Download the results
aws s3 cp "${query_results_uri}" ./lims_manifest.csv
```

Using the lims manifest we can now generate the package.

By using the `--wait` parameter, the CLI will only return once the package has been completed. 

This may take around 5 mins to complete depending on the size of the package.

```bash
data-sharing-tool generate-package \
  --lims-manifest-csv lims_manifest.csv \
  --wait
```

This will generate a package and print the package to the console like so:

```bash
Generating package 'pkg.123456789'...
```

For the workflow manifest, we can use the same query as above, but we will need to change the final table name to 'workflow'.  

An example of the SQL might be as follows:

```sql
/*
Get the libraries associated with the project 'CUP' and their sequencing run date is greater than or equal to '2025-04-01'.
*/
WITH libraries AS (
    SELECT library_id
    FROM lims 
    WHERE 
      project_id = 'CUP' AND
      sequencing_run_date >= CAST('2025-04-01' AS DATE)
)
/*
Select matching TN workflows for the libraries above 
*/
SELECT *
from workflow 
WHERE 
    workflow_name = 'tumor-normal' AND
    library_id IN (SELECT library_id FROM libraries)
```


## Package Validation

Once the package has completed generating we can validate the package using the following command:

> By using the BROWSER env var, the package report will be automatically opened up in our browser!

```bash
data-sharing-tool view-package-report \
  --package-id pkg.12345678910
```

Look through the metadata, fastq and secondary analysis tabs to ensure that the package is correct.  


## Package Sharing

### Pushing Packages

We can use the following command to push the package to a destination location.  This will generate a push job id.

Like the package generation, we can use the `--wait` parameter to wait for the job to complete.

```bash
data-sharing-tool push-package \
  --package-id pkg.12345678910 \
  --share-location s3://bucket/path-to-prefix/
```

### Presigning packages

Not all data receivers will have an S3 bucket or ICAV2 project for us to dump data in.  

Therefore we also support the old-school presigned url method.  

We can use the following command to generate presigned urls in a script for the package

```bash
data-sharing-tool presign-package \
  --package-id pkg.12345678910
```

This will return a presigned url for a shell script that can be used to download the package.
