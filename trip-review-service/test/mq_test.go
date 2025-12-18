package test

import (
	"context"
	"fmt"
	"github.com/apache/rocketmq-clients/golang"
	"github.com/apache/rocketmq-clients/golang/credentials"
	"log"
	"testing"
	"time"
)

//func TestMQ(t *testing.T) {
//
//	review := domain.Review{
//		ID:         "2328",
//		UserID:     "12",
//		TargetType: "hotel",
//		TargetID:   "12",
//		Rating:     1,
//		Text:       "哈基米南北绿豆",
//		Images:     nil,
//		CreatedAt:  time.Time{},
//		UpdatedAt:  time.Time{},
//	}
//	producer := mq.GetMQ()
//	err := producer.SendMessage("TestTopic", review.ToString(), "TestTag")
//	if err != nil {
//		return
//	}
//
//}

const (
	Topic     = "TestTopic"
	GroupName = "xxxxxx"
	Endpoint  = "127.0.0.1:8081"
	AccessKey = "xxxxxx"
	SecretKey = "xxxxxx"
)

var (
	// maximum waiting time for receive func
	awaitDuration = time.Second * 5
	// maximum number of messages received at one time
	maxMessageNum int32 = 16
	// invisibleDuration should > 20s
	invisibleDuration = time.Second * 20
	// receive messages in a loop
)

func TestConsumer(t *testing.T) {
	simpleConsumer, err := golang.NewSimpleConsumer(&golang.Config{
		Endpoint:      Endpoint,
		ConsumerGroup: "tripsphere",
		Credentials: &credentials.SessionCredentials{
			AccessKey:    AccessKey,
			AccessSecret: SecretKey,
		},
	},
		golang.WithAwaitDuration(awaitDuration),
		golang.WithSubscriptionExpressions(map[string]*golang.FilterExpression{
			Topic: golang.SUB_ALL,
		}),
	)
	if err != nil {
		log.Fatal(err)
	}
	// start simpleConsumer
	err = simpleConsumer.Start()
	if err != nil {
		log.Fatal(err)
	}
	// gracefule stop simpleConsumer
	defer simpleConsumer.GracefulStop()

	go func() {
		for {
			fmt.Println("start recevie message")
			mvs, err := simpleConsumer.Receive(context.TODO(), maxMessageNum, invisibleDuration)
			if err != nil {
				fmt.Println(err)
			}
			// ack message
			for _, mv := range mvs {
				simpleConsumer.Ack(context.TODO(), mv)
				fmt.Println(string(mv.GetBody()))
			}
			fmt.Println("wait a moment")
			fmt.Println()
			time.Sleep(time.Second * 3)
		}
	}()
	// run for a while
	time.Sleep(time.Minute)
}
