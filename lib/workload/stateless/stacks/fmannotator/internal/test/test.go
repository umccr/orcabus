package test

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"github.com/docker/go-connections/nat"
	"github.com/go-testfixtures/testfixtures/v3"
	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/stretchr/testify/require"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator/schema/orcabus_workflowmanager/workflowrunstatechange"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"testing"
)

type S3Object struct {
	EventType    string         `db:"event_type"`
	Bucket       string         `db:"bucket"`
	Key          string         `db:"key"`
	EventTime    sql.NullTime   `db:"event_time"`
	Size         sql.NullInt64  `db:"size"`
	StorageClass sql.NullString `db:"storage_class"`
}

func setupService(t *testing.T, buildContext string, port nat.Port, wait wait.Strategy, env map[string]string) (string, nat.Port) {
	ctx := context.Background()

	args := make(map[string]*string)
	for k, v := range env {
		args[k] = &v
	}

	containerName := strings.ReplaceAll(strings.Trim(buildContext, "./"), "/", "_")
	req := testcontainers.ContainerRequest{
		FromDockerfile: testcontainers.FromDockerfile{
			Context:   buildContext,
			Repo:      containerName,
			Tag:       containerName,
			BuildArgs: args,
			KeepImage: true,
		},
		ExposedPorts: []string{port.Port()},
		Env:          env,
		WaitingFor:   wait,
		Name:         containerName,
	}
	container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: req,
		Started:          true,
		Reuse:            true,
	})
	require.NoError(t, err)
	t.Cleanup(func() {
		require.NoError(t, container.Terminate(ctx))
	})

	ip, err := container.Host(ctx)
	require.NoError(t, err)
	port, err = container.MappedPort(ctx, port)
	require.NoError(t, err)

	fmt.Printf("setup `%v` at `%v:%v`\n", containerName, ip, port.Port())

	return ip, port
}

func SetupFileManager(t *testing.T) *sql.DB {
	// This has to be such a large timeout because FM needs to compile/build with access to a Postgres database. If
	// the timeout is too low, before the FM compilation connects to the database, testcontainers will kill the postgres
	// container as there are no connections to it.
	// This is another good reason to remove the requirement to compile with a database, as most software doesn't
	// expect this to be the case.
	t.Setenv("TESTCONTAINERS_RYUK_CONNECTION_TIMEOUT", "10m")
	t.Setenv("TESTCONTAINERS_RYUK_RECONNECTION_TIMEOUT", "5m")

	// Database
	testDatabaseName := fmt.Sprintf("filemanager_test_%v", strings.ReplaceAll(uuid.New().String(), "-", "_"))
	databaseIp, port := setupService(t, "../filemanager/database", "4321", wait.ForLog("database system is ready to accept connections").
		WithOccurrence(2),
		map[string]string{
			"POSTGRES_DB":       testDatabaseName,
			"POSTGRES_USER":     "filemanager",
			"POSTGRES_PASSWORD": "filemanager", // pragma: allowlist secret
			"PGPORT":            "4321",
		})

	// API
	intPort, err := strconv.Atoi(port.Port())
	require.NoError(t, err)

	databaseFmt := "postgresql://filemanager:filemanager@%v:%v/%v?sslmode=disable" // pragma: allowlist secret
	databaseUrl := fmt.Sprintf(databaseFmt, "host.docker.internal", intPort, testDatabaseName)
	ip, port := setupService(t, "../filemanager", "8000", wait.ForHTTP("/api/v1/s3/count"),
		map[string]string{
			"DATABASE_URL": databaseUrl,
		})

	fmEndpoint := fmt.Sprintf("http://%v:%v", ip, port.Port())
	databaseEndpoint := fmt.Sprintf(databaseFmt, databaseIp, intPort, testDatabaseName)

	t.Setenv("FMANNOTATOR_FILE_MANAGER_ENDPOINT", fmEndpoint)
	t.Setenv("FMANNOTATOR_FILE_MANAGER_SECRET_NAME", "secret")

	return loadFixtures(t, databaseEndpoint)
}

func loadFixtures(t *testing.T, databaseUrl string) *sql.DB {
	var err error
	db, err := sql.Open("postgres", databaseUrl)
	require.NoError(t, err)

	fixtures, err := testfixtures.New(
		testfixtures.Database(db),
		testfixtures.Dialect("postgres"),
		testfixtures.Directory(fixturesPath()),
	)
	require.NoError(t, err)

	fmt.Printf("loading data into test database: %v\n", databaseUrl)

	err = fixtures.Load()
	require.NoError(t, err)

	return db
}

func fixturesPath() string {
	_, file, _, _ := runtime.Caller(0)
	return filepath.Join(filepath.Dir(file), "../../fixtures")
}

func CreateEvent(t *testing.T, path string) workflowrunstatechange.Event {
	b, err := os.ReadFile(filepath.Join(fixturesPath(), path))
	require.NoError(t, err)

	var event workflowrunstatechange.Event
	err = json.Unmarshal(b, &event)
	require.NoError(t, err)

	return event
}

func QueryObjects(t *testing.T, db *sql.DB, query string) []S3Object {
	var s3Objects []S3Object
	err := sqlx.NewDb(db, "postgres").Unsafe().Select(&s3Objects, query)
	require.NoError(t, err)

	return s3Objects
}
