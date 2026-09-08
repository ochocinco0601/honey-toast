// Coverage probe — Java. Every line marked PROBE is an idiom a real estate can use to do
// the thing named. This file is NOT a positive control:
// it is deliberately full of idioms no rule covers yet, and `probe.py` reports which.
//
// Marker form:  // PROBE:<fact_kind>:<framework>:<name>
// The probe belongs to the next non-blank, non-comment line.

package probe;

class Java {

    // ---------------------------------------------------------------- inbound
    // PROBE:inbound_route:spring-mvc:GetMapping
    @GetMapping("/a")
    void a() {}

    // PROBE:inbound_route:spring-mvc:RequestMapping
    @RequestMapping("/b")
    void b() {}

    // PROBE:inbound_route:jaxrs:Path-GET
    @Path("/c")
    @GET
    void c() {}

    // PROBE:inbound_route:servlet:WebServlet
    @WebServlet("/d")
    class D extends HttpServlet {}

    // PROBE:inbound_route:spring-graphql:QueryMapping
    @QueryMapping
    Object e() { return null; }

    // PROBE:inbound_route:grpc-spring:GrpcService
    @GrpcService
    class F {}

    // PROBE:inbound_route:spring-webflux:RouterFunction
    RouterFunction<ServerResponse> routes() {
        return RouterFunctions.route(RequestPredicates.GET("/g"), this::handle);
    }

    // ---------------------------------------------------------------- outbound
    // PROBE:outbound_http:spring:RestTemplate-exchange
    void h() { restTemplate.exchange("http://x", null, null, String.class); }

    // PROBE:outbound_http:spring:WebClient-uri
    void i() { webClient.get().uri("http://x").retrieve(); }

    // PROBE:outbound_http:spring-cloud:FeignClient
    @FeignClient(name = "customers")
    interface CustomersClient {
        @GetMapping("/owners/{id}")
        Object owner(String id);
    }

    // PROBE:outbound_http:jdk:HttpClient-send
    void j() throws Exception { java.net.http.HttpClient.newHttpClient().send(request, handler); }

    // PROBE:outbound_http:okhttp:newCall-execute
    void k() throws Exception { okHttpClient.newCall(request).execute(); }

    // PROBE:outbound_http:apache:HttpClient-execute
    void l() throws Exception { closeableHttpClient.execute(httpGet); }

    // ---------------------------------------------------------------- durable
    // PROBE:durable_write:spring-data:repository-save
    void m() { orderRepository.save(order); }

    // PROBE:durable_read:spring-data:repository-findBy
    void n() { orderRepository.findByStatus("new"); }

    // PROBE:durable_write:jpa:EntityManager-persist
    void o() { entityManager.persist(order); }

    // PROBE:durable_read:spring-jdbc:JdbcTemplate-query
    void p() { jdbcTemplate.query("SELECT * FROM orders", mapper); }

    // PROBE:durable_write:spring-jdbc:JdbcTemplate-update
    void q() { jdbcTemplate.update("UPDATE orders SET status = ?", "done"); }

    // PROBE:durable_read:mybatis:mapper-select
    void r() { orderMapper.selectByPrimaryKey(1L); }

    // PROBE:durable_write:mongo:MongoTemplate-save
    void s() { mongoTemplate.save(order); }

    // PROBE:durable_read:mongo:MongoTemplate-find
    void t() { mongoTemplate.find(query, Order.class); }

    // PROBE:durable_read:jdbc:PreparedStatement-executeQuery
    void u() throws Exception { connection.prepareStatement("SELECT 1").executeQuery(); }

    // PROBE:durable_write:r2dbc:DatabaseClient-sql
    void v() { databaseClient.sql("INSERT INTO orders VALUES (?)").then(); }

    // ---------------------------------------------------------------- messaging
    // PROBE:message_consumer:spring-kafka:KafkaListener
    @KafkaListener(topics = "orders")
    void w(String m) {}

    // PROBE:message_consumer:spring-amqp:RabbitListener
    @RabbitListener(queues = "orders")
    void x(String m) {}

    // PROBE:message_consumer:jms:JmsListener
    @JmsListener(destination = "orders")
    void y(String m) {}

    // PROBE:message_publisher:spring-kafka:KafkaTemplate-send
    void z() { kafkaTemplate.send("orders", "payload"); }

    // PROBE:message_consumer:spring-cloud-stream:functional-Consumer
    @Bean
    java.util.function.Consumer<String> orders() { return message -> {}; }

    // PROBE:message_publisher:spring-cloud-stream:StreamBridge
    void aa() { streamBridge.send("orders-out", "payload"); }

    // ---------------------------------------------------------------- batch and schedule
    // PROBE:background_trigger:spring:Scheduled
    @Scheduled(fixedDelay = 1000)
    void ab() {}

    // PROBE:background_trigger:spring-batch:JobBuilder
    void ac() { new JobBuilder("job", jobRepository).start(step).build(); }

    // PROBE:background_trigger:spring-batch:Tasklet
    class Ad implements Tasklet {
        public RepeatStatus execute(StepContribution c, ChunkContext ctx) { return null; }
    }

    // PROBE:durable_read:spring-batch:JdbcCursorItemReader
    void ae() { new JdbcCursorItemReader<Order>(); }

    // PROBE:durable_write:spring-batch:JdbcBatchItemWriter
    void af() { new JdbcBatchItemWriter<Order>(); }

    // PROBE:background_trigger:quartz:Job-execute
    class Ag implements org.quartz.Job {
        public void execute(JobExecutionContext context) {}
    }

    // ---------------------------------------------------------------- config
    // PROBE:env_read:spring:Value-placeholder
    @Value("${orders.host}")
    String ah;

    // PROBE:config_ref:spring:ConfigurationProperties
    @ConfigurationProperties(prefix = "orders")
    class Ai {}

    // PROBE:config_ref:spring:Environment-getProperty
    void aj() { environment.getProperty("orders.host"); }

    // PROBE:env_read:jdk:System-getenv
    void ak() { System.getenv("ORDERS_HOST"); }
}

// ---------------------------------------------------------------- naming, not just types
// **The same idioms under the field names people actually use.** A receiver constraint is a bet
// on naming convention, and these are the spellings that lose it. Found on a real
// Spring Kafka estate: all four publish sites inject the template into a field called `template`,
// and the publisher rule saw none of them.
class JavaNaming {

    private KafkaTemplate<Long, Order> template;
    private RestTemplate rest;

    // PROBE:message_publisher:spring-kafka:bare-template-send
    void publishThroughBareName() { template.send("orders", 1L, order); }

    // PROBE:outbound_http:spring:bare-rest-name
    void callThroughBareName() { rest.getForObject("http://customers/api", String.class); }
}

// Kafka Streams declares sources on a builder, not through an annotation.
class JavaStreams {
    // PROBE:message_consumer:kafka-streams:builder-stream
    void topology(StreamsBuilder builder) { builder.stream("orders"); }
}
