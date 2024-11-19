import gzip
import logging
import os
from typing import Dict, List, Any, Tuple, LiteralString

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
        self.url = os.getenv("PG_DD_URL")
        self.databases = self.read_databases()
        self.logger = logger

    def csvs_for_tables(self) -> Dict[str, Dict[str, str]]:
        """
        Get csvs for all tables in all databases.
        """

        databases = {}
        for entry in self.databases.values():
            url = f"{self.url}/{entry['database']}"

            conn: psycopg.connection.Connection
            with psycopg.connect(url) as conn:
                if entry.get("sql_dump") is not None:
                    tables = [(i, e, True) for i, e in enumerate(entry["sql_dump"])]
                else:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            select table_name from information_schema.tables
                            where table_schema='public';
                            """
                        )
                        tables = [(name[0], name[0], False) for name in cur.fetchall()]
                        self.logger.info(f"fetched table names: {tables}")

                with conn.cursor() as cur:
                    databases[entry["database"]] = self.copy_tables_to_csv(cur, tables)

        return databases

    def load_table(self, table, data, conn, only_non_empty=True):
        """
        Load a table with the CSV data.
        """

        with conn.cursor() as cur:
            if only_non_empty:
                exists = cur.execute(
                    sql.SQL(
                        """
                    select exists(
                        select from pg_tables where tablename = '{}'
                    );
                    """
                    ).format(sql.SQL(table))
                ).fetchone()[0]
                has_records = cur.execute(
                    sql.SQL(
                        """
                    select exists(select * from {})
                    """
                    ).format(sql.SQL(table))
                ).fetchone()[0]

                if not exists or has_records:
                    return

            with cur.copy(
                sql.SQL(
                    """
                    copy {} from stdin with (format csv, header);
                    """
                ).format(sql.Identifier(table)),
            ) as copy:
                copy.write(data)

    def target_files(self) -> List[Tuple[str, str, str, str]]:
        """
        Get the target files for all directories.
        """

        files = []
        for database, tables in self.csvs_for_tables().items():
            for table, value in tables.items():
                file = f"{database}/{table}.csv.gz"
                files += [(database, table, file, value)]
        return files

    @staticmethod
    def read_databases() -> Dict[str, Dict[str, Any]]:
        """
        Read the databases to dump from env variables.
        """

        prefix = "PG_DD_DATABASE_"
        sql_dump_prefix = "_SQL_DUMP"
        sql_load_prefix = "_SQL_LOAD"
        variables = {}
        for key, value in os.environ.items():
            if key[: len(prefix)] == prefix:
                database = key[len(prefix) :]
                suffix_dump = database[-len(sql_dump_prefix) :]
                suffix_load = database[-len(sql_load_prefix) :]

                database = database.removesuffix(sql_dump_prefix).removesuffix(
                    sql_load_prefix
                )
                variables.setdefault(database, {})

                if suffix_dump == sql_dump_prefix:
                    variables[database]["sql_dump"] = [
                        s.strip() for s in value.split(",")
                    ]
                elif suffix_load == sql_load_prefix:
                    variables[database]["sql_load"] = [
                        s.strip() for s in value.split(",")
                    ]
                else:
                    variables[database]["database"] = database.lower()

        return variables

    @staticmethod
    def copy_tables_to_csv(
        cur: psycopg.cursor.Cursor, tables: List[Tuple[str, str, bool]]
    ) -> Dict[str, str]:
        """
        Get tables as a csv string.
        """

        csvs = {}
        for name, table, is_statement in tables:
            if is_statement:
                statement = sql.SQL(
                    """
                    copy ({}) to stdout with (format csv, header);
                    """
                )
            else:
                statement = sql.SQL(
                    """
                    copy {} to stdout with (format csv, header);
                    """
                )

            rows = []
            copy: psycopg.Copy
            table: LiteralString = table
            with cur.copy(statement.format(sql.SQL(table))) as copy:
                for row in copy:
                    rows += [row.tobytes().decode("utf-8")]

            csvs[name] = "".join(rows)

        return csvs


class PgDDLocal(PgDD):
    """
    Dump CSV files to a local directory.
    """

    def __init__(self, logger=logging.getLogger(__name__)):
        super().__init__(logger=logger)
        self.out = os.getenv("PG_DD_DIR")
        self.bucket = os.getenv("PG_DD_BUCKET")
        self.prefix = os.getenv("PG_DD_PREFIX")
        self.s3: S3ServiceResource = boto3.resource("s3")

    def write_to_dir(self):
        """
        Write the CSV files to the output directory.
        """

        for _, _, f, value in self.target_files():
            file = f"{self.out}/{f}"
            os.makedirs(file.rsplit("/", 1)[0], exist_ok=True)
            self.logger.info(f"writing to file: {f}")

            with open(file, "wb") as f:
                f.write(gzip.compress(str.encode(value)))

    def load_to_database(self):
        """
        Download from S3 CSV files to load.
        """

        def load_files():
            for root, _, files in os.walk(f"{self.out}/{database}"):
                for file in files:
                    with open(f"{root}/{file}", "rb") as f:
                        table = file.removesuffix(".csv.gz")
                        load = self.databases[database.upper()].get("sql_load")
                        if load is not None:
                            table = load[int(table)]

                        self.load_table(
                            table, gzip.decompress(f.read()).decode("utf-8"), conn
                        )

        for _, dirs, _ in os.walk(self.out):
            for database in dirs:
                conn: psycopg.connection.Connection
                with psycopg.connect(f"{self.url}/{database}") as conn:
                    conn.set_deferrable(True)
                    load_files()
                    conn.commit()


class PgDDS3(PgDD):
    """
    Commands related to running this inside a Lambda function.
    """

    def __init__(self, logger=logging.getLogger(__name__)):
        super().__init__(logger=logger)
        self.bucket = os.getenv("PG_DD_BUCKET")
        self.prefix = os.getenv("PG_DD_PREFIX")
        self.dir = os.getenv("PG_DD_DIR")
        self.s3: S3ServiceResource = boto3.resource("s3")

    def write_to_bucket(self):
        """
        Write the CSV files to the S3 bucket.
        """

        for _, _, key, value in self.target_files():
            if self.prefix:
                key = f"{self.prefix}/{key}"

            self.logger.info(f"writing to bucket with key: {key}")

            s3_object = self.s3.Object(self.bucket, key)
            s3_object.put(Body=gzip.compress(str.encode(value)))

    def download_local(self):
        """
        Download from S3 CSV files to load.
        """

        for _, _, f, _ in self.target_files():
            self.logger.info(f"target file: {f}")
            file = f"{self.dir}/{f}"
            os.makedirs(file.rsplit("/", 1)[0], exist_ok=True)

            s3_object = self.s3.Object(self.bucket, f"{self.prefix}/{f}")
            s3_object.download_file(f"{self.dir}/{f}")
