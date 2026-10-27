// Coverage probe — .NET. Deliberately full of idioms no rule may cover yet.
// Marker form:  // PROBE:<fact_kind>:<framework>:<name>

namespace Probe;

class Dotnet
{
    // ---------------------------------------------------------------- inbound
    // PROBE:inbound_route:aspnet-mvc:HttpGet
    [HttpGet("a")]
    public void A() { }

    // PROBE:inbound_route:aspnet-mvc:Route
    [Route("b")]
    public void B() { }

    // PROBE:inbound_route:aspnet-minimal:MapGet
    public void C(WebApplication app) { app.MapGet("/c", () => "x"); }

    // PROBE:inbound_route:aspnet-minimal:MapPost
    public void D(WebApplication app) { app.MapPost("/d", () => "x"); }

    // PROBE:inbound_route:signalr:Hub
    public class ChatHub : Hub
    {
        public Task Send(string m) => Task.CompletedTask;
    }

    // PROBE:inbound_route:azure-functions:FunctionName
    [FunctionName("ProcessOrder")]
    public void E([QueueTrigger("orders")] string message) { }

    // ---------------------------------------------------------------- outbound
    // PROBE:outbound_http:httpclient:GetAsync
    public async Task F(HttpClient c) { await c.GetAsync("http://x"); }

    // PROBE:outbound_http:httpclient:GetFromJsonAsync
    public async Task G(HttpClient c) { await c.GetFromJsonAsync<string>("http://x"); }

    // PROBE:outbound_http:refit:interface
    public interface ICatalogApi
    {
        [Get("/items")]
        Task<string> GetItems();
    }

    // PROBE:outbound_http:grpc:client-call
    public async Task H(Basket.BasketClient client) { await client.GetBasketAsync(new GetBasketRequest()); }

    // ---------------------------------------------------------------- durable
    // PROBE:durable_write:efcore:SaveChangesAsync
    public async Task I(DbContext ctx) { await ctx.SaveChangesAsync(); }

    // PROBE:durable_write:efcore:DbSet-Add
    public void J(DbContext ctx, Order o) { ctx.Set<Order>().Add(o); }

    // PROBE:durable_read:efcore:DbSet-FirstOrDefaultAsync
    public async Task K(DbContext ctx) { await ctx.Set<Order>().FirstOrDefaultAsync(); }

    // PROBE:durable_read:efcore:DbSet-Where
    public void L(DbContext ctx) { ctx.Set<Order>().Where(o => o.Id > 0).ToList(); }

    // PROBE:durable_read:dapper:QueryAsync
    public async Task M(IDbConnection c) { await c.QueryAsync<Order>("SELECT * FROM orders"); }

    // PROBE:durable_write:dapper:ExecuteAsync
    public async Task N(IDbConnection c) { await c.ExecuteAsync("UPDATE orders SET status = 1"); }

    // PROBE:durable_write:ado:SqlCommand-ExecuteNonQuery
    public void O(SqlConnection c) { new SqlCommand("UPDATE orders SET status = 1", c).ExecuteNonQuery(); }

    // PROBE:durable_read:ado:SqlCommand-ExecuteReader
    public void P(SqlConnection c) { new SqlCommand("SELECT 1", c).ExecuteReader(); }

    // PROBE:durable_write:mongo:InsertOneAsync
    public async Task Q(IMongoCollection<Order> col, Order o) { await col.InsertOneAsync(o); }

    // PROBE:durable_read:mongo:FindAsync
    public async Task R(IMongoCollection<Order> col) { await col.FindAsync(x => true); }

    // ---------------------------------------------------------------- messaging
    // PROBE:message_consumer:masstransit:IConsumer
    public class OrderConsumer : IConsumer<OrderSubmitted>
    {
        public Task Consume(ConsumeContext<OrderSubmitted> context) => Task.CompletedTask;
    }

    // PROBE:message_publisher:masstransit:Publish
    public async Task S(IPublishEndpoint bus) { await bus.Publish(new OrderSubmitted()); }

    // PROBE:message_publisher:masstransit:Send
    public async Task T(ISendEndpoint endpoint) { await endpoint.Send(new OrderSubmitted()); }

    // PROBE:message_consumer:rabbitmq-client:BasicConsume
    public void U(IModel channel) { channel.BasicConsume("orders", true, consumer); }

    // PROBE:message_publisher:rabbitmq-client:BasicPublish
    public void V(IModel channel) { channel.BasicPublish("ex", "orders", null, body); }

    // PROBE:message_consumer:confluent-kafka:Consume
    public void W(IConsumer<string, string> consumer) { consumer.Consume(); }

    // PROBE:message_publisher:confluent-kafka:ProduceAsync
    public async Task X(IProducer<string, string> p) { await p.ProduceAsync("orders", message); }

    // PROBE:message_consumer:azure-servicebus:ProcessMessageAsync
    public void Y(ServiceBusProcessor processor) { processor.ProcessMessageAsync += Handler; }

    // ---------------------------------------------------------------- background
    // PROBE:background_trigger:aspnet:BackgroundService-ExecuteAsync
    public class Worker : BackgroundService
    {
        protected override Task ExecuteAsync(CancellationToken t) => Task.CompletedTask;
    }

    // PROBE:background_trigger:aspnet:IHostedService-StartAsync
    public class Hosted : IHostedService
    {
        public Task StartAsync(CancellationToken t) => Task.CompletedTask;
        public Task StopAsync(CancellationToken t) => Task.CompletedTask;
    }

    // PROBE:background_trigger:hangfire:RecurringJob
    public void Z() { RecurringJob.AddOrUpdate("job", () => Console.WriteLine("x"), Cron.Hourly()); }

    // PROBE:background_trigger:quartz:IJob-Execute
    public class QJob : IJob
    {
        public Task Execute(IJobExecutionContext context) => Task.CompletedTask;
    }

    // ---------------------------------------------------------------- config
    // PROBE:config_ref:aspnet:GetSection
    public void Aa(IConfiguration cfg) { cfg.GetSection("Orders"); }

    // PROBE:config_ref:aspnet:GetConnectionString
    public void Ab(IConfiguration cfg) { cfg.GetConnectionString("OrdersDb"); }

    // PROBE:config_ref:aspnet:IOptions
    public void Ac(IServiceCollection s, IConfiguration cfg) { s.Configure<OrderOptions>(cfg.GetSection("Orders")); }

    // PROBE:env_read:dotnet:GetEnvironmentVariable
    public void Ad() { Environment.GetEnvironmentVariable("ORDERS_HOST"); }

    // ---------------------------------------------------------------- client wiring
    // PROBE:client_binding:aspnet:AddHttpClient
    public void Ae(IServiceCollection s) { s.AddHttpClient<CatalogService>(); }

    // PROBE:client_binding:aspnet:AddGrpcClient
    public void Af(IServiceCollection s) { s.AddGrpcClient<Basket.BasketClient>(); }
}

// The publish wrapper an event-bus abstraction puts in front of the broker. The send is here,
// not at the line where the event object is constructed.
class DotnetPublishing
{
    // PROBE:message_publisher:eventbus-wrapper:PublishThroughEventBusAsync
    public async Task Publish(IIntegrationEventService svc, IntegrationEvent evt)
    {
        await svc.PublishThroughEventBusAsync(evt);
    }

    // The seam both ends of the topology depend on: the send names a variable and the type is
    // only on the line that bound it. This is the shape every eShop publish site actually has.
    public async Task PublishConcrete(IIntegrationEventService svc, int orderId)
    {
        // PROBE:event_binding:dotnet:integration-event-construction
        var orderStartedEvent = new OrderStartedIntegrationEvent(orderId);
        await svc.PublishThroughEventBusAsync(orderStartedEvent);
    }
}
