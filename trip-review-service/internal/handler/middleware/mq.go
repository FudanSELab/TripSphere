package middleware

import (
	"context"
	"fmt"
	"github.com/apache/rocketmq-clients/golang"
	"github.com/apache/rocketmq-clients/golang/credentials"
	"log"
	"trip-review-service/configs"
)

type MQ struct {
	producer golang.Producer
}

func (m *MQ) SendMessage(topic string, body string, tag string) error {

	if topic == "" {
		log.Println("missing topic in msg: ", body)
		return nil
	}

	msg := &golang.Message{
		Topic: topic,
		Body:  []byte(body),
	}
	msg.SetKeys()
	msg.SetTag(tag)

	log.Println("sending msg", body, " to", topic)
	resp, err := m.producer.Send(context.TODO(), msg)
	if err != nil {
		return err
	}
	for i := 0; i < len(resp); i++ {
		fmt.Printf("%#v\n", resp[i])
	}
	//m.producer.SendAsync(context.TODO(), msg, func(ctx context.Context, resp []*golang.SendReceipt, err error) {
	//	if err != nil {
	//		log.Println("failed to send message:", err)
	//	}
	//	log.Println("success to send message ")
	//	for i := 0; i < len(resp); i++ {
	//		fmt.Printf("%#v\n", resp[i])
	//	}
	//})
	return nil
}

var mq *MQ

func GetMQ() *MQ {
	return mq
}

func init() {
	config := configs.GetConfig()

	producer, err := golang.NewProducer(&golang.Config{
		Endpoint: config.RocketMQ.Endpoint,
		Credentials: &credentials.SessionCredentials{
			AccessKey:    config.RocketMQ.AccessKey,
			AccessSecret: config.RocketMQ.SecretKey,
		},
	},
	)
	if err != nil {
		log.Println("failed to create rocketmq producer:", err)
	}
	log.Println("success to create rocketmq producer")
	mq = &MQ{producer: producer}

	err = mq.producer.Start()
	if err != nil {
		log.Println("failed to start rocketmq producer:", err)
	}

}
