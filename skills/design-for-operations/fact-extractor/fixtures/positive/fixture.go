package fixtures

import (
	"net/http"
	"os"
)

func register(r *http.ServeMux, s *grpc.Server, srv OrderServer) {
	r.HandleFunc("/orders", handle)
	r.Handle("/health", nil)
	pb.RegisterOrderServiceServer(s, srv)
}

func (s *server) GetOrder(ctx context.Context, req *pb.GetOrderRequest) (*pb.GetOrderResponse, error) {
	return nil, nil
}

func callOut(c *http.Client, client pb.OrderServiceClient) {
	c.Get("http://ledger/api")
	c.Post("http://ledger/api", "application/json", nil)
	c.Do(nil)
	os.Getenv("ORDERS_HOST")
	os.LookupEnv("ORDERS_HOST")
}
