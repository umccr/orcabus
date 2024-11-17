import os

from pg_dd.pg_dd import PgDDS3, PgDDLocal


def main():
    if os.getenv("PG_DD_BUCKET"):
        PgDDS3().write_to_bucket()
    else:
        PgDDLocal().write_to_dir()


if __name__ == "__main__":
    main()
