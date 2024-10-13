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
	"github.com/testcontainers/testcontainers-go/modules/compose"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator/schema/orcabus_workflowmanager/workflowrunstatechange"
	"os"
	"path"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

// S3Object Represents a mock S3Object.
type S3Object struct {
	EventType    string          `db:"event_type"`
	Bucket       string          `db:"bucket"`
	Key          string          `db:"key"`
	EventTime    sql.NullTime    `db:"event_time"`
	Size         sql.NullInt64   `db:"size"`
	StorageClass sql.NullString  `db:"storage_class"`
	Attributes   json.RawMessage `db:"attributes"`
}

// SetupFileManager Setup the filemanager for testing.
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
	databaseFmt := "postgresql://filemanager:filemanager@%v:%v/%v?sslmode=disable" // pragma: allowlist secret

	dockerCompose, err := compose.NewDockerComposeWith(compose.WithStackFiles("../filemanager/compose.yml"), compose.StackIdentifier("filemanager"))
	require.NoError(t, err)
	stack := dockerCompose.WithEnv(map[string]string{
		"POSTGRES_DB":  testDatabaseName,
		"DATABASE_URL": fmt.Sprintf(databaseFmt, "postgres", 4321, testDatabaseName),
	})

	t.Cleanup(func() {
		require.NoError(t, stack.Down(ctx))
	})

	require.NoError(t, stack.Up(ctx, compose.Wait(true)))

	ip, port := serviceEndpoint(t, stack, "postgres", "4321")
	databaseEndpoint := fmt.Sprintf(databaseFmt, ip, port, testDatabaseName)

	ip, port = serviceEndpoint(t, stack, "api", "8000")
	fmEndpoint := fmt.Sprintf("http://%v:%v", ip, port)

	t.Setenv("FMANNOTATOR_FILE_MANAGER_ENDPOINT", fmEndpoint)
	t.Setenv("FMANNOTATOR_FILE_MANAGER_SECRET_NAME", "secret")

	return loadFixtures(t, databaseEndpoint)
}

// CreateEvent Create a mock test event.
func CreateEvent(t *testing.T, path string) workflowrunstatechange.Event {
	b, err := os.ReadFile(filepath.Join(fixturesPath(), path))
	require.NoError(t, err)

	var event workflowrunstatechange.Event
	err = json.Unmarshal(b, &event)
	require.NoError(t, err)

	return event
}

// QueryObjects Query the database objects.
func QueryObjects(t *testing.T, db *sql.DB, query string) []S3Object {
	var s3Objects []S3Object
	err := sqlx.NewDb(db, "postgres").Unsafe().Select(&s3Objects, query)
	require.NoError(t, err)

	return s3Objects
}

func fixturesPath() string {
	_, file, _, _ := runtime.Caller(0)
	return filepath.Join(filepath.Dir(file), "../../fixtures")
}

func serviceEndpoint(t *testing.T, stack compose.ComposeStack, serviceName string, port nat.Port) (string, string) {
	ctx := context.Background()
	service, err := stack.ServiceContainer(ctx, serviceName)
	require.NoError(t, err)

	ip, err := service.Host(ctx)
	require.NoError(t, err)
	port, err = service.MappedPort(ctx, port)
	require.NoError(t, err)

	return ip, port.Port()
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
