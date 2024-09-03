package fmannotator

import "github.com/kelseyhightower/envconfig"

// Config Configuration for the fmannotator
type Config struct {
	FileManagerEndpoint string `required:"true" split_words:"true"`
	FileManagerSecret   string `required:"true" split_words:"true"`
}

// LoadConfig Load config from the environment.
func LoadConfig() (Config, error) {
	var config Config
	err := envconfig.Process("fmannotator", &config)
	return config, err
}
