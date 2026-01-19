package middleware

import (
	"context"
	"fmt"
	"log"

	"github.com/apache/rocketmq-clients/golang"
	"github.com/apache/rocketmq-clients/golang/credentials"

	"trip-review-service/config"
)

type message struct {
	Topic string
	Body  string
	Tag   string
}

func (m *message) GetMsg() *golang.Message {
	if m.Topic == "" {
		log.Println("missing topic in msg: ", m.Body)
		return nil
	}
	msg := &golang.Message{
		Topic: m.Topic,
		Body:  []byte(m.Body),
	}
	msg.SetKeys()
	msg.SetTag(m.Tag)
	return msg
}

type MQ struct {
	Producer    golang.Producer
	messageChan chan *message
}

func (m *MQ) AddMessage(topic, body, tag string) {
	msg := &message{
		Topic: topic,
		Body:  body,
		Tag:   tag,
	}
	m.messageChan <- msg
	log.Println("added msg", msg.Body, " to channel")
}

func (m *MQ) SendMessage() {

	go func() {
		for msg := range m.messageChan {
			log.Println("sending msg", msg.Body, " to", msg.Topic)

			resp, err := m.Producer.Send(context.TODO(), msg.GetMsg())
			if err != nil {
				log.Println("failed to send message:", err)
			}

			for i := range resp {
				fmt.Printf("%#v\n", resp[i])
			}
		}
	}()

	//m.producer.SendAsync(context.TODO(), msg, func(ctx context.Context, resp []*golang.SendReceipt, err error) {
	//	if err != nil {
	//		log.Println("failed to send message:", err)
	//	}
	//	log.Println("success to send message ")
	//	for i := 0; i < len(resp); i++ {
	//		fmt.Printf("%#v\n", resp[i])
	//	}
	//})
	//return nil
}

var mq *MQ

func GetMQ() *MQ {
	return mq
}

func init() {
	// Initialize config first
	config.Init()

	// Skip if RocketMQ endpoint is not configured
	if config.RocketMQEndpoint == "" || config.RocketMQEndpoint == "localhost:8081" {
		log.Println("RocketMQ endpoint not configured, skipping producer initialization")
		return
	}

	producer, err := golang.NewProducer(&golang.Config{
		Endpoint: config.RocketMQEndpoint,
		Credentials: &credentials.SessionCredentials{
			AccessKey:    config.RocketMQAccessKey,
			AccessSecret: config.RocketMQSecretKey,
		},
	})
	if err != nil {
		log.Println("failed to create rocketmq producer:", err)
		return
	}
	log.Println("success to create rocketmq producer")
	mq = &MQ{Producer: producer, messageChan: make(chan *message, 1024)}

	err = mq.Producer.Start()
	if err != nil {
		log.Println("failed to start rocketmq producer:", err)
		return
	}
	log.Println("success to start rocketmq producer")

	mq.SendMessage()
	log.Println("waiting to send message")
}
