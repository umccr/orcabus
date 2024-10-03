// Package fmannotator config using environment variables.
package fmannotator

import (
	"github.com/kelseyhightower/envconfig"
	"log/slog"
	"os"
)

const (
	EnvPrefix = "fmannotator"
)

// Config Configuration for the fmannotator
type Config struct {
	FileManagerEndpoint   string `required:"true" split_words:"true"`
	FileManagerSecretName string `required:"true" split_words:"true"`
}

// LoadConfig Load config from the environment.
func LoadConfig() (Config, error) {
	var config Config
	err := envconfig.Process(EnvPrefix, &config)
	return config, err
}

func GetLogLevel() (slog.Level, error) {
	var level slog.Level
	err := level.UnmarshalText([]byte(os.Getenv("GO_LOG")))
	return level, err
}
