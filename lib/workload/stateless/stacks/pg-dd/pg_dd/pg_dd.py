import os
from typing import Dict, List, Any

import boto3
import psycopg
from psycopg import sql
from mypy_boto3_s3 import S3ServiceResource

from dotenv import load_dotenv

load_dotenv()


class PgDD:
    def __init__(self):
        self.databases = self.read_databases()

    @staticmethod
    def read_databases() -> Dict[str, Dict[str, Any]]:
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
        database_url = os.getenv("PG_DD_URL")
        databases = {}
        for entry in self.databases.values():
            url = database_url.rsplit("/", 1)[0]
            url = f"{url}/{entry['database']}"

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

                with conn.cursor() as cur:
                    databases[entry["database"]] = self.copy_tables_to_csv(cur, tables)

        return databases


class PgDDLocal(PgDD):
    def __init__(self):
        super().__init__()
        self.out = os.getenv("PG_DD_DIR")

    def write_to_dir(self) -> None:
        for database, tables in self.csvs_for_tables().items():
            output_dir = f"{self.out}/{database}"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            for table, value in tables.items():
                with open(f"{self.out}/{database}/{table}.csv", "w") as f:
                    f.write(value)


class PgDDS3(PgDD):
    def __init__(self):
        super().__init__()
        self.bucket = os.getenv("PG_DD_BUCKET")
        self.prefix = os.getenv("PG_DD_PREFIX")

    def write_to_bucket(self) -> None:
        s3: S3ServiceResource = boto3.resource("s3")
        for database, tables in self.csvs_for_tables().items():
            for table, value in tables.items():
                key = f"{database}/{table}.csv"

                if self.prefix:
                    key = f"{self.prefix}/{key}"

                s3_object = s3.Object(self.bucket, key)
                s3_object.put(Body=value)


def handler():
    PgDDS3().write_to_bucket()
