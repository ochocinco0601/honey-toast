namespace Fixtures;

public class Fixture
{
    private HttpClient _client;
    private OrderContext _ctx;
    private IConfiguration _cfg;

    [HttpGet("orders/{id}")]
    public async Task<Order> Get(int id) => await _ctx.Orders.FindAsync(id);

    [HttpPost("orders")]
    public async Task Create(Order o) { await _ctx.SaveChangesAsync(); }

    [HttpPut("orders/{id}")]
    public void Replace(Order o) { _ctx.SaveChanges(); }

    [HttpDelete("orders/{id}")]
    public void Drop(int id) { }

    [HttpPatch("orders/{id}")]
    public void Patch(int id) { }

    [Route("legacy")]
    public void Legacy() { }

    public async Task CallOut()
    {
        await _client.GetAsync("http://catalog/api");
        await _client.PostAsync("http://catalog/api", null);
        await _client.PutAsync("http://catalog/api", null);
        await _client.DeleteAsync("http://catalog/api");
        await _client.SendAsync(null);
        await _client.GetFromJsonAsync<Order>("http://catalog/api");
        await _client.PostAsJsonAsync("http://catalog/api", new Order());
    }

    public void Config()
    {
        _cfg.GetSection("Orders");
        _cfg.GetValue<int>("Orders:Timeout");
        _cfg.GetConnectionString("OrdersDb");
        Environment.GetEnvironmentVariable("ORDERS_HOST");
    }

    public void Publish() { var e = new OrderStartedIntegrationEvent(); }

    public void Background()
    {
        Task.Run(() => { });
        var t = new Timer(null);
    }
}

public class OrderStartedHandler : IIntegrationEventHandler<OrderStartedIntegrationEvent>
{
    public Task Handle(OrderStartedIntegrationEvent e) => Task.CompletedTask;
}

public class OrderWorker : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken token) { await Task.Delay(1); }
}

public class Wiring
{
    public void Register(IServiceCollection services, IEventBus bus)
    {
        services.AddHttpClient<CatalogService>();
        services.AddGrpcClient<Basket.BasketClient>();
        bus.AddSubscription<OrderStartedIntegrationEvent, OrderStartedHandler>();
    }
}

public class BasketGrpc
{
    public override Task<CustomerBasketResponse> GetBasket(GetBasketRequest request, ServerCallContext context)
        => Task.FromResult(new CustomerBasketResponse());
}
