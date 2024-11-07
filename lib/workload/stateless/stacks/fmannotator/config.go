// Package fmannotator config using environment variables.
package fmannotator

import (
	"encoding/json"
	"github.com/aws/aws-secretsmanager-caching-go/secretcache"
	"github.com/kelseyhightower/envconfig"
	"log/slog"
	"os"
)

const (
	EnvPrefix    = "fmannotator"
	TokenIdField = "id_token"
)

// Config Configuration for the fmannotator
type Config struct {
	FileManagerEndpoint   string `required:"true" split_words:"true"`
	FileManagerSecretName string `required:"true" split_words:"true"`
	QueueName             string `required:"true" split_words:"true"`
	QueueMaxMessages      int32  `required:"true" split_words:"true"`
	QueueWaitTimeSecs     int32  `required:"true" split_words:"true"`
}

// LoadConfig Load config from the environment.
func LoadConfig() (Config, error) {
	var config Config
	err := envconfig.Process(EnvPrefix, &config)
	return config, err
}

// GetLogLevel get the log level from an environment variable.
func GetLogLevel() (slog.Level, error) {
	var level slog.Level
	err := level.UnmarshalText([]byte(os.Getenv("GO_LOG")))
	return level, err
}

// LoadCachedConfig load config and cached secrets.
func LoadCachedConfig(secretCache *secretcache.Cache) (*Config, string, error) {
	level, err := GetLogLevel()
	if err != nil {
		return nil, "", err
	}
	slog.SetLogLoggerLevel(level)

	config, err := LoadConfig()
	if err != nil {
		return nil, "", err
	}

	secret, err := secretCache.GetSecretString(config.FileManagerSecretName)
	if err != nil {
		return nil, "", err
	}

	secretKeys := make(map[string]string)
	err = json.Unmarshal([]byte(secret), &secretKeys)
	if err != nil {
		return nil, "", err
	}

	return &config, secretKeys[TokenIdField], nil
}
