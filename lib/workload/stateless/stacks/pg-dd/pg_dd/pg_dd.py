import gzip
import logging
import os
from typing import Dict, List, Any

import boto3
import psycopg
from psycopg import sql
from mypy_boto3_s3 import S3ServiceResource

from dotenv import load_dotenv

load_dotenv()


class PgDD:
    """
    A class to dump postgres databases to CSV files.
    """

    def __init__(self, logger=logging.getLogger(__name__)):
        self.databases = self.read_databases()
        self.logger = logger

    @staticmethod
    def read_databases() -> Dict[str, Dict[str, Any]]:
        """
        Read the databases to dump from env variables.
        """

        prefix = "PG_DD_DATABASE_"
        sql_prefix = "_SQL"
        variables = {}
        for key, value in os.environ.items():
            if key[: len(prefix)] == prefix:
                database = key[len(prefix) :]
                suffix = database[-len(sql_prefix) :]
                database = database.removesuffix(sql_prefix)
                variables.setdefault(database, {})

                if suffix == sql_prefix:
                    variables[database]["sql"] = [s.strip() for s in value.split(",")]
                else:
                    variables[database]["database"] = database.lower()

        return variables

    @staticmethod
    def copy_tables_to_csv(
        cur: psycopg.cursor.Cursor, tables: List[str]
    ) -> Dict[str, str]:
        """
        Get tables as a csv string.
        """

        csvs = {}
        for table in tables:
            rows = []
            copy: psycopg.Copy
            with cur.copy(
                sql.SQL(
                    """
                    copy {} to stdout with (format csv, header);
                    """
                ).format(sql.Identifier(table))
            ) as copy:
                for row in copy:
                    rows += [row.tobytes().decode("utf-8")]

            csvs[table] = "".join(rows)

        return csvs

    def csvs_for_tables(self) -> Dict[str, Dict[str, str]]:
        """
        Get csvs for all tables in all databases.
        """

        database_url = os.getenv("PG_DD_URL")
        databases = {}
        for entry in self.databases.values():
            url = f"{database_url}/{entry['database']}"

            conn: psycopg.connection.Connection
            with psycopg.connect(url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        select table_name from information_schema.tables
                        where table_schema='public';
                        """
                    )
                    tables = [name[0] for name in cur.fetchall()]
                    self.logger.debug(f"fetched table names: {tables}")

                with conn.cursor() as cur:
                    databases[entry["database"]] = self.copy_tables_to_csv(cur, tables)

        return databases


class PgDDLocal(PgDD):
    """
    Dump CSV files to a local directory.
    """

    def __init__(self, logger=logging.getLogger(__name__)):
        super().__init__(logger=logger)
        self.out = os.getenv("PG_DD_DIR")

    def write_to_dir(self) -> None:
        """
        Write the CSV files to the output directory.
        """

        for database, tables in self.csvs_for_tables().items():
            output_dir = f"{self.out}/{database}"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            self.logger.debug(f"writing to directory: {output_dir}")

            for table, value in tables.items():
                with open(f"{self.out}/{database}/{table}.csv.gz", "wb") as f:
                    f.write(gzip.compress(str.encode(value)))


class PgDDS3(PgDD):
    """
    Dump CSV files to an S3 bucket.
    """

    def __init__(self, logger=logging.getLogger(__name__)):
        super().__init__(logger=logger)
        self.bucket = os.getenv("PG_DD_BUCKET")
        self.prefix = os.getenv("PG_DD_PREFIX")

    def write_to_bucket(self) -> None:
        """
        Write the CSV files to the S3 bucket.
        """

        s3: S3ServiceResource = boto3.resource("s3")
        for database, tables in self.csvs_for_tables().items():
            for table, value in tables.items():
                key = f"{database}/{table}.csv.gz"

                if self.prefix:
                    key = f"{self.prefix}/{key}"

                self.logger.debug(f"writing to bucket with key: {key}")

                s3_object = s3.Object(self.bucket, key)
                s3_object.put(Body=gzip.compress(str.encode(value)))
