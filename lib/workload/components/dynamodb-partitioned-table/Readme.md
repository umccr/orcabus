# Dynamodb Icav2 Table

The cornerstone of every ICAv2 deployment service.  

This template will generate a dynamodb table to run with the step function constructs (build this table in the stateful stack).

This table will be used to store the states of the icav2 analysis.

## Inputs

All that is required is a table name.

## Notes

Each service should build their own table.

Step functions from the icav2 handle event change stack and icav2 ready event handler stack will interact with the database.  

