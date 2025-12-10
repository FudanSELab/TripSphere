package configs

import (
	"github.com/BurntSushi/toml"
	"log"
	"time"
)

type Config struct {
	MySQL struct {
		Read struct {
			Addr string `toml:"addr"`
			User string `toml:"user"`
			Pass string `toml:"pass"`
			Name string `toml:"name"`
		} `toml:"read"`
		Write struct {
			Addr string `toml:"addr"`
			User string `toml:"user"`
			Pass string `toml:"pass"`
			Name string `toml:"name"`
		} `toml:"write"`
		Base struct {
			MaxOpenConn     int           `toml:"maxOpenConn"`
			MaxIdleConn     int           `toml:"maxIdleConn"`
			ConnMaxLifeTime time.Duration `toml:"connMaxLifeTime"`
		} `toml:"base"`
	} `toml:"mysql"`
}

var config *Config
var configPath string

func init() {
	config = new(Config)
	configPath = "./configs/pro_configs.toml"
	err := LoadConfig()
	if err != nil {
		log.Println("fail to read config files while initializing:", err)
		return
	}
	log.Println("success to read config files")
}

func LoadConfig() error {
	_, err := toml.DecodeFile(configPath, config)
	if err != nil {
		log.Println("fail to read config files:", err)
		return err
	}
	return nil
}
func GetConfig() *Config {
	return config
}
