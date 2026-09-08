# Coverage probe - Python. Deliberately full of idioms no rule may cover yet.
# Marker form:  # PROBE:<fact_kind>:<framework>:<name>

# ---------------------------------------------------------------- inbound
# PROBE:inbound_route:flask:route
@app.route("/a")
def a():
    pass


# PROBE:inbound_route:fastapi:get
@app.get("/b")
def b():
    pass


# PROBE:inbound_route:fastapi:put
@app.put("/c")
def c():
    pass


# PROBE:inbound_route:fastapi:APIRouter-post
@router.post("/d")
def d():
    pass


# PROBE:inbound_route:django:urls-path
urlpatterns = [path("e/", view_e)]

# PROBE:inbound_route:django:urls-re_path
more_patterns = [re_path(r"^f/$", view_f)]

# PROBE:inbound_route:drf:router-register
router.register(r"orders", OrderViewSet)


# PROBE:inbound_route:grpc:add_servicer_to_server
def register(server):
    orders_pb2_grpc.add_OrderServiceServicer_to_server(OrderService(), server)


# ---------------------------------------------------------------- outbound
# PROBE:outbound_http:requests:get
def g():
    requests.get("http://x")


# PROBE:outbound_http:httpx:get
def h():
    httpx.get("http://x")


# PROBE:outbound_http:aiohttp:session-get
async def i(session):
    await session.get("http://x")


# PROBE:outbound_http:urllib:urlopen
def j():
    urllib.request.urlopen("http://x")


# ---------------------------------------------------------------- durable
# PROBE:durable_write:sqlalchemy:session-commit
def k(session):
    session.commit()


# PROBE:durable_read:sqlalchemy:session-query
def l(session):
    session.query(Order).all()


# PROBE:durable_read:sqlalchemy2:session-execute-select
def m(session):
    session.execute(select(Order))


# PROBE:durable_read:django-orm:objects-filter
def n():
    Order.objects.filter(status="new")


# PROBE:durable_write:django-orm:objects-create
def o():
    Order.objects.create(status="new")


# PROBE:durable_write:django-orm:instance-save
def p(order):
    order.save()


# PROBE:durable_read:psycopg:cursor-execute
def q(conn):
    conn.cursor().execute("SELECT * FROM orders")


# PROBE:durable_write:pymongo:insert_one
def r(collection):
    collection.insert_one({"status": "new"})


# PROBE:durable_read:pymongo:find_one
def s(collection):
    collection.find_one({"status": "new"})


# PROBE:durable_read:oracle:cursor-execute
def t(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM dual")


# ---------------------------------------------------------------- messaging
# PROBE:message_consumer:kafka-python:KafkaConsumer
def u():
    consumer = KafkaConsumer("orders")


# PROBE:message_publisher:kafka-python:producer-send
def v(producer):
    producer.send("orders", b"payload")


# PROBE:message_consumer:confluent-kafka:subscribe
def w(consumer):
    consumer.subscribe(["orders"])


# PROBE:message_consumer:pika:basic_consume
def x(channel):
    channel.basic_consume(queue="orders", on_message_callback=handler)


# PROBE:message_publisher:pika:basic_publish
def y(channel):
    channel.basic_publish(exchange="", routing_key="orders", body=b"payload")


# ---------------------------------------------------------------- background and ETL
# PROBE:background_trigger:celery:shared_task
@shared_task
def z():
    pass


# PROBE:background_trigger:celery:app-task
@app.task
def aa():
    pass


# PROBE:background_trigger:threading:Thread
def ab():
    threading.Thread(target=aa).start()


# PROBE:background_trigger:apscheduler:BackgroundScheduler
def ac():
    BackgroundScheduler()


# PROBE:background_trigger:airflow:DAG
def ad():
    with DAG("orders_etl", schedule_interval="@daily") as dag:
        pass


# PROBE:background_trigger:airflow:task-decorator
@task
def ae():
    pass


# PROBE:background_trigger:airflow:PythonOperator
def af():
    PythonOperator(task_id="extract", python_callable=ae)


# ---------------------------------------------------------------- config
# PROBE:env_read:os:environ-get
def ag():
    os.environ.get("ORDERS_HOST")


# PROBE:env_read:os:getenv
def ah():
    os.getenv("ORDERS_HOST")


# PROBE:config_ref:flask:app-config
def ai():
    return app.config["ORDERS_BACKEND"]


# PROBE:config_ref:django:settings
def aj():
    return settings.ORDERS_BACKEND


# PROBE:config_ref:pydantic:BaseSettings
class Settings(BaseSettings):
    orders_host: str
