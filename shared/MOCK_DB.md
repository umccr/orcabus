# Mock DB using PostgreSQL

From your compose stack root, preform:

```
docker compose up -d
docker compose ps
```

```
docker exec -e PGPASSWORD=orcabus -it orcabus_db psql -h 0.0.0.0 -d orcabus -U orcabus
```

```
orcabus# \l
orcabus# \c orcabus
orcabus# \d
orcabus# \dt
orcabus# select count(1) from your_table_name;
orcabus# \q
```
