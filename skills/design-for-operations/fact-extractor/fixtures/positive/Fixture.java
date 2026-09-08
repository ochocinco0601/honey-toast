package fixtures;

import org.springframework.beans.factory.annotation.Value;

public class Fixture {
    private OrderRepository orderRepository;
    private javax.persistence.EntityManager em;
    private org.springframework.web.client.RestTemplate restTemplate;
    private org.springframework.web.reactive.function.client.WebClient webClient;

    @Value("${orders.endpoint}")
    private String endpoint;

    @Value("${orders.POLL.interval:5000}")
    private String pollInterval;

    @GetMapping("/orders/{id}")
    public Order get(String id) { return orderRepository.findById(id); }

    @PostMapping("/orders")
    public Order create(Order o) { return orderRepository.save(o); }

    @PutMapping("/orders/{id}")
    public Order replace(Order o) { return orderRepository.saveAll(o); }

    @DeleteMapping("/orders/{id}")
    public void drop(String id) { orderRepository.delete(id); }

    @PatchMapping("/orders/{id}")
    public void patch(String id) { em.merge(id); }

    @RequestMapping("/legacy")
    public void legacy() { em.persist(new Order()); }

    public void callOut() {
        restTemplate.exchange("http://customers/api", null, null, String.class);
        restTemplate.getForObject("http://customers/api", String.class);
        restTemplate.getForEntity("http://customers/api", String.class);
        restTemplate.postForObject("http://customers/api", null, String.class);
        restTemplate.postForEntity("http://customers/api", null, String.class);
        webClient.get().uri("http://visits/api").retrieve();
    }

    public String env() { return System.getenv("ORDERS_HOST"); }

    @Scheduled(fixedDelay = 5000)
    public void poll() { new Thread(() -> {}).start(); }

    @Async
    public void background() { }
}
