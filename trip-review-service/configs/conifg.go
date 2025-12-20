package configs

import (
	"fmt"
	"github.com/BurntSushi/toml"
	"github.com/fsnotify/fsnotify"
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

	RocketMQ struct {
		GroupName string `toml:"groupName"`
		Endpoint  string `toml:"endpoint"`
		AccessKey string `toml:"accessKey"`
		SecretKey string `toml:"secretKey"`
	} `toml:"rocketmq"`
}

var config *Config
var configPath string

func init() {
	config = new(Config)
	configPath = "../configs/pro_configs.toml"
	err := LoadConfig(configPath)
	if err != nil {
		log.Println("fail to read config files while initializing:", err)
		return
	}
	log.Println("success to read config files while initializing")
	WatchConfig(configPath)
}

func WatchConfig(path string) {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		log.Println("failed to create config watcher", err)
	}
	err = watcher.Add(path)
	if err != nil {
		log.Printf("failed to add config file (%s) to watcher: %s", path, err)
	}
	go func() {
		for {
			select {
			case event, ok := <-watcher.Events:
				if !ok {
					return
				}
				fmt.Printf("config file event happened: %s\n", event)

				if event.Op&fsnotify.Create == fsnotify.Create {
					fmt.Printf("Config File was created: %s\n", event.Name)
				}
				if event.Op&fsnotify.Write == fsnotify.Write {
					fmt.Printf("Config File was updated: %s\n", event.Name)
				}
				if event.Op&fsnotify.Remove == fsnotify.Remove {
					fmt.Printf("Config File was deleted: %s\n", event.Name)
				}
				if event.Op&fsnotify.Rename == fsnotify.Rename {
					fmt.Printf("Config File was: %s\n", event.Name)
				}
			case err, ok := <-watcher.Errors:
				if !ok {
					return
				}
				log.Println("an error happened with watcher:", err)
			}
		}
	}()

}

func LoadConfig(path string) error {
	_, err := toml.DecodeFile(path, config)
	if err != nil {
		log.Println("fail to read config files:", err)
		return err
	}

	return nil
}
func GetConfig() *Config {
	return config
}
