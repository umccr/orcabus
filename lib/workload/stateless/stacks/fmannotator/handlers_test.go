package fmannotator

import (
	"database/sql"
	"fmt"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/require"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator/internal/test"
	"testing"
	"time"
)

type TestCase struct {
	event       string
	portalRunId string
	expected    []test.S3Object
}

func successCase(location *time.Location) TestCase {
	return TestCase{"event_succeeded.json", "202409021221e6e6", []test.S3Object{
		{
			EventType:    "Created",
			Bucket:       "bucket",
			Key:          "byob-icav2/development/analysis/wts/202409021221e6e6/_manifest.json",
			EventTime:    sql.NullTime{Time: time.Date(2024, 9, 2, 0, 0, 0, 0, location), Valid: true},
			Size:         sql.NullInt64{Int64: 5, Valid: true},
			StorageClass: sql.NullString{String: "Standard", Valid: true},
		},
		{
			EventType:    "Deleted",
			Bucket:       "bucket",
			Key:          "byob-icav2/development/analysis/wts/202409021221e6e6/_manifest.json",
			EventTime:    sql.NullTime{Time: time.Date(2024, 9, 3, 0, 0, 0, 0, location), Valid: true},
			Size:         sql.NullInt64{},
			StorageClass: sql.NullString{},
		},
		{
			EventType:    "Created",
			Bucket:       "bucket",
			Key:          "byob-icav2/development/analysis/wts/202409021221e6e6/_tags.json",
			EventTime:    sql.NullTime{Time: time.Date(2024, 9, 4, 0, 0, 0, 0, location), Valid: true},
			Size:         sql.NullInt64{Int64: 10, Valid: true},
			StorageClass: sql.NullString{String: "Standard", Valid: true},
		},
	}}
}

func failCase(location *time.Location) TestCase {
	return TestCase{"event_failed.json", "202409021221e6c6", []test.S3Object{
		{
			EventType:    "Created",
			Bucket:       "bucket",
			Key:          "byob-icav2/development/analysis/wts/202409021221e6c6/_manifest.json",
			EventTime:    sql.NullTime{Time: time.Date(2024, 9, 5, 0, 0, 0, 0, location), Valid: true},
			Size:         sql.NullInt64{Int64: 3, Valid: true},
			StorageClass: sql.NullString{String: "Standard", Valid: true},
		},
		{
			EventType:    "Deleted",
			Bucket:       "bucket",
			Key:          "byob-icav2/development/analysis/wts/202409021221e6c6/_manifest.json",
			EventTime:    sql.NullTime{Time: time.Date(2024, 9, 6, 0, 0, 0, 0, location), Valid: true},
			Size:         sql.NullInt64{},
			StorageClass: sql.NullString{},
		},
	}}
}

func TestHandler(t *testing.T) {
	db := test.SetupFileManager(t)

	location, err := time.LoadLocation("Etc/UTC")
	require.NoError(t, err)

	testCases := []TestCase{successCase(location), failCase(location)}

	for _, tc := range testCases {
		t.Run(fmt.Sprintf("%v", tc.event), func(t *testing.T) {
			event := test.CreateEvent(t, tc.event)

			config, err := LoadConfig()
			require.NoError(t, err)

			err = PortalRunId(event, &config, "token")
			require.NoError(t, err)

			s3Objects := test.QueryObjects(t, db, fmt.Sprintf("select * from s3_object where key like '%%%v%%'", tc.portalRunId))
			require.Equal(t, tc.expected, s3Objects)
		})
	}
}
