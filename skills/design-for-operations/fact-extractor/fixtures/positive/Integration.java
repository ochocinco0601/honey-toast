package fixtures;

// Brokers. A listener wakes on another service's message, which is a message_consumer and
// not a background_trigger; these two were conflated in an earlier version of the rule set.
public class Integration {

    private KafkaTemplate<String, String> kafkaTemplate;
    private JmsTemplate jmsTemplate;
    private RabbitTemplate rabbitTemplate;

    @KafkaListener(topics = "orders")
    public void onOrder(String message) { }

    @RabbitListener(queues = "orders")
    public void onRabbit(String message) { }

    @JmsListener(destination = "orders")
    public void onJms(String message) { }

    @StreamListener("orders-in")
    public void onStream(String message) { }

    @ServiceActivator(inputChannel = "orders")
    public void onChannel(String message) { }

    public void publish() {
        kafkaTemplate.send("orders", "payload");
        kafkaTemplate.sendDefault("payload");
        jmsTemplate.convertAndSend("orders", "payload");
    }
}

// Apache Camel. The component scheme in the endpoint URI is what names the fact kind.
class OrderRoutes extends RouteBuilder {
    @Override
    public void configure() {
        from("kafka:orders")
            .to("http://ledger/api/post")
            .to("jms:queue:settlement");

        from("timer:poll?period=5000")
            .to("kafka:audit");

        from("platform-http:/orders")
            .to("https://catalog/api");

        // In-process wiring. Must not be read as a service boundary.
        from("direct:internal")
            .to("direct:next")
            .to("seda:async");
    }
}

// Spring Batch. A job is work initiated by something other than a request.
class BatchConfig {

    @Bean
    public Job importOrders(JobRepository jobRepository, Step step) {
        return new JobBuilder("importOrders", jobRepository).start(step).build();
    }

    @Bean
    @StepScope
    public Step step(JobRepository jobRepository, PlatformTransactionManager tx) {
        return new StepBuilder("step", jobRepository).build();
    }
}
