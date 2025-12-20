package test

import (
	"testing"
	"time"
	"trip-review-service/internal/domain"
	mq "trip-review-service/internal/handler/middleware"
)

func TestMQ(t *testing.T) {

	review := domain.Review{
		ID:         "2328",
		UserID:     "12",
		TargetType: "hotel",
		TargetID:   "1569",
		Rating:     1,
		Text:       "px love ai ,llm is his favorite",
		Images:     nil,
		CreatedAt:  time.Time{},
		UpdatedAt:  time.Time{},
	}
	mq.GetMQ().AddMessage("ReviewTopic", review.ToString(), "CreateReview")

	select {}
	//msg := &golang.Message{Topic: "ReviewTopic", Body: []byte(review.ToString())}
	//msg.SetTag("CreateReview")
	//resp, err := mq.GetMQ().Producer.Send(context.TODO(), msg)
	//if err != nil {
	//	log.Println("failed to send message:", err)
	//}
	//
	//for i := 0; i < len(resp); i++ {
	//	fmt.Printf("%#v\n", resp[i])
	//}
}

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

//func TestConsumer(t *testing.T) {
//	simpleConsumer, err := golang.NewSimpleConsumer(&golang.Config{
//		Endpoint:      Endpoint,
//		ConsumerGroup: "tripsphere",
//		Credentials: &credentials.SessionCredentials{
//			AccessKey:    AccessKey,
//			AccessSecret: SecretKey,
//		},
//	},
//		golang.WithAwaitDuration(awaitDuration),
//		golang.WithSubscriptionExpressions(map[string]*golang.FilterExpression{
//			Topic: golang.SUB_ALL,
//		}),
//	)
//	if err != nil {
//		log.Fatal(err)
//	}
//	// start simpleConsumer
//	err = simpleConsumer.Start()
//	if err != nil {
//		log.Fatal(err)
//	}
//	// gracefule stop simpleConsumer
//	defer simpleConsumer.GracefulStop()
//
//	go func() {
//		for {
//			fmt.Println("start recevie message")
//			mvs, err := simpleConsumer.Receive(context.TODO(), maxMessageNum, invisibleDuration)
//			if err != nil {
//				fmt.Println(err)
//			}
//			// ack message
//			for _, mv := range mvs {
//				simpleConsumer.Ack(context.TODO(), mv)
//				fmt.Println(string(mv.GetBody()))
//			}
//			fmt.Println("wait a moment")
//			fmt.Println()
//			time.Sleep(time.Second * 3)
//		}
//	}()
//	// run for a while
//	time.Sleep(time.Minute)
//}
