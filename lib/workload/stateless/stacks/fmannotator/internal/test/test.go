package test

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"github.com/go-testfixtures/testfixtures/v3"
	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/stretchr/testify/require"
	"github.com/testcontainers/testcontainers-go/modules/compose"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator/schema/orcabus_workflowmanager/workflowrunstatechange"
	"io"
	"os"
	"path"
	"path/filepath"
	"runtime"
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

func SetupFileManager(t *testing.T) *sql.DB {
	t.Setenv("TESTCONTAINERS_RYUK_CONNECTION_TIMEOUT", "10m")
	t.Setenv("TESTCONTAINERS_RYUK_RECONNECTION_TIMEOUT", "5m")

	ctx := context.Background()

	// This works around an issue in test containers which requires the presence of a config.json file.
	dir := t.TempDir()
	err := os.WriteFile(path.Join(dir, "config.json"), []byte("{}"), 0666)
	require.NoError(t, err)
	t.Setenv("DOCKER_CONFIG", dir)

	testDatabaseName := fmt.Sprintf("filemanager_test_%v", strings.ReplaceAll(uuid.New().String(), "-", "_"))

	dockerCompose, err := compose.NewDockerComposeWith(compose.WithStackFiles("../filemanager/compose.yml"), compose.StackIdentifier("filemanager"))
	stack := dockerCompose.WithEnv(map[string]string{
		"POSTGRES_DB": testDatabaseName,
		"API_PORT":    "8000",
	})
	require.NoError(t, err)

	t.Cleanup(func() {
		ctx := context.Background()
		for _, service := range stack.Services() {
			container, err := stack.ServiceContainer(ctx, service)
			if err != nil {
				t.Logf("failed to get container for service %q: %v", service, err)
				continue
			}
			logs, err := container.Logs(ctx)
			if err != nil {
				t.Logf("failed to get logs for service %q: %v", service, err)
				continue
			}
			buf, err := io.ReadAll(logs)
			if err != nil {
				t.Logf("failed to read logs for service %q: %v", service, err)
				continue
			}
			t.Logf("[%s]\n%s", service, string(buf))
		}

		require.NoError(t, stack.Down(ctx))
	})

	require.NoError(t, stack.Up(ctx, compose.Wait(true)))

	database, err := stack.ServiceContainer(ctx, "postgres")

	require.NoError(t, err)
	ip, err := database.Host(ctx)
	require.NoError(t, err)
	port, err := database.MappedPort(ctx, "4321")
	require.NoError(t, err)
	databaseEndpoint := fmt.Sprintf("postgresql://filemanager:filemanager@%v:%v/%v?sslmode=disable", ip, port.Port(), testDatabaseName)

	api, err := stack.ServiceContainer(ctx, "api")
	require.NoError(t, err)
	ip, err = api.Host(ctx)
	require.NoError(t, err)
	port, err = api.MappedPort(ctx, "8000")
	require.NoError(t, err)

	fmEndpoint := fmt.Sprintf("http://%v:%v", ip, port.Port())
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
