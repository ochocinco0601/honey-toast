import axios from 'axios';

@Entity('order')
export class OrderEntity {}

@Controller('orders')
export class OrderController {
  constructor(
    @InjectRepository(OrderEntity)
    private readonly orderRepository: Repository<OrderEntity>,
    private readonly http: HttpClient,
  ) {}

  @Get()
  findAll() { return this.orderRepository.find(); }

  @Get(':id')
  findOne(id: string) { return this.orderRepository.findOne(id); }

  @Post()
  create(o: OrderEntity) { return this.orderRepository.save(o); }

  @Put(':id')
  replace(o: OrderEntity) { return this.orderRepository.update(o); }

  @Delete(':id')
  drop(id: string) { return this.orderRepository.delete(id); }

  @Patch(':id')
  patch(id: string) { return this.orderRepository.upsert(id); }

  @All('legacy')
  legacy() { return this.orderRepository.remove(1); }

  outbound() {
    this.http.get('/orders');
    this.http.post('/orders', {});
    this.http.put('/orders/1', {});
    this.http.delete('/orders/1');
    this.http.patch('/orders/1', {});
    this.http.request('GET', '/orders');
    axios('/orders');
    fetch('/orders');
  }

  prisma(prisma: any) {
    prisma.order.findMany();
    prisma.order.findUnique({});
    prisma.order.findFirst({});
    prisma.order.count();
    prisma.order.create({});
    prisma.order.insert({});
    this.orderRepository.createQueryBuilder('o');
    this.orderModel.findById('1');
  }

  @EventPattern('order.created')
  onCreated() {}

  @MessagePattern('order.get')
  onGet() {}

  @OnEvent('order.paid')
  onPaid() {}

  @Cron('0 * * * *')
  hourly() {}

  @Interval(5000)
  every() {}

  @Timeout(1000)
  once() {}

  timer() { setInterval(() => {}, 1000); }

  env() { return process.env.ORDERS_HOST; }
}
