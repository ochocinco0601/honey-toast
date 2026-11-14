// Coverage probe — JavaScript and TypeScript. Deliberately full of idioms no rule may cover.
// Marker form:  // PROBE:<fact_kind>:<framework>:<name>

// ---------------------------------------------------------------- inbound
// PROBE:inbound_route:express:app-get
app.get('/a', handler);

// PROBE:inbound_route:express:router-post
router.post('/b', handler);

// PROBE:inbound_route:nestjs:Get-decorator
class NestController {
  // PROBE:inbound_route:nestjs:Post-decorator
  @Post('c')
  create() {}

  @Get('d')
  read() {}
}

// PROBE:inbound_route:fastify:route-get
fastify.get('/e', handler);

// PROBE:inbound_route:koa:router-get
koaRouter.get('/f', handler);

// PROBE:inbound_route:grpc-node:addService
grpcServer.addService(proto.OrderService.service, {});

// PROBE:inbound_route:nextjs:route-handler
export async function GET(request: Request) { return new Response('x'); }

// ---------------------------------------------------------------- outbound
// PROBE:outbound_http:angular:HttpClient-get
class AngularService {
  constructor(private http: HttpClient) {}
  load() { return this.http.get('/orders'); }
}

// PROBE:outbound_http:axios:get
axios.get('/orders');

// PROBE:outbound_http:fetch:global
fetch('/orders');

// PROBE:outbound_http:nestjs:HttpService-get
class NestOutbound {
  constructor(private readonly httpService: HttpService) {}
  load() { return this.httpService.get('/orders'); }
}

// PROBE:outbound_http:got:get
got.get('https://orders');

// PROBE:outbound_http:superagent:request-get
superagent.get('/orders');

// ---------------------------------------------------------------- durable
// PROBE:durable_read:typeorm:repository-findOne
declare const orderRepository: any;
orderRepository.findOne({ id: 1 });

// PROBE:durable_write:typeorm:repository-save
orderRepository.save({ id: 1 });

// PROBE:durable_read:typeorm:createQueryBuilder
orderRepository.createQueryBuilder('o');

// PROBE:durable_read:prisma:findMany
prisma.order.findMany();

// PROBE:durable_write:prisma:create
prisma.order.create({ data: {} });

// PROBE:durable_read:mongoose:Model-find
OrderModel.find({ status: 'new' });

// PROBE:durable_write:mongoose:document-save
orderDoc.save();

// PROBE:durable_read:sequelize:findAll
Order.findAll({ where: { status: 'new' } });

// PROBE:durable_write:sequelize:create
Order.create({ status: 'new' });

// PROBE:durable_read:node-postgres:pool-query
pool.query('SELECT * FROM orders');

// PROBE:durable_read:mssql:request-query
sqlRequest.query('SELECT * FROM orders');

// PROBE:durable_read:knex:select
knex('orders').select('*');

// ---------------------------------------------------------------- messaging
// PROBE:message_consumer:nestjs:EventPattern
class NestConsumer {
  @EventPattern('order.created')
  onCreated() {}
}

// PROBE:message_consumer:kafkajs:consumer-run
kafkaConsumer.run({ eachMessage: async () => {} });

// PROBE:message_consumer:kafkajs:consumer-subscribe
kafkaConsumer.subscribe({ topic: 'orders' });

// PROBE:message_publisher:kafkajs:producer-send
kafkaProducer.send({ topic: 'orders', messages: [] });

// PROBE:message_consumer:amqplib:channel-consume
amqpChannel.consume('orders', handler);

// PROBE:message_publisher:amqplib:channel-sendToQueue
amqpChannel.sendToQueue('orders', Buffer.from('x'));

// ---------------------------------------------------------------- background
// PROBE:background_trigger:nestjs:Cron
class Scheduled {
  @Cron('0 * * * *')
  hourly() {}
}

// PROBE:background_trigger:node:setInterval
setInterval(() => {}, 1000);

// PROBE:background_trigger:bullmq:Worker
new Worker('orders', async () => {});

// PROBE:background_trigger:node-cron:schedule
cron.schedule('0 * * * *', () => {});

// ---------------------------------------------------------------- config
// PROBE:env_read:node:process-env
const host = process.env.ORDERS_HOST;

// PROBE:config_ref:nestjs:ConfigService-get
class Configured {
  constructor(private config: ConfigService) {}
  read() { return this.config.get('ORDERS_HOST'); }
}

// PROBE:config_ref:angular:environment
const apiUrl = environment.apiUrl;

// PROBE:durable_write:mongoose:Model-updateOne
OrderModel.updateOne({ _id: 1 }, { status: 'done' });

// PROBE:durable_write:mongoose:Model-deleteOne
OrderModel.deleteOne({ _id: 1 });

// PROBE:durable_write:mongodb-driver:collection-insertMany
ordersCollection.insertMany([{ status: 'new' }]);

// PROBE:durable_write:mongodb-driver:collection-bulkWrite
ordersCollection.bulkWrite([]);
