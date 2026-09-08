import os
import threading

import httpx
import requests
from flask import Flask

app = Flask(__name__)


@app.route("/orders")
def list_orders():
    return app.config["ORDERS_BACKEND"]


@app.get("/orders/<oid>")
def get_order(oid):
    return app.config.get("ORDERS_BACKEND")


@app.post("/orders")
def create_order():
    requests.post("http://ledger/api")
    requests.get("http://ledger/api")
    requests.put("http://ledger/api")
    requests.delete("http://ledger/api")
    requests.patch("http://ledger/api")
    httpx.get("http://ledger/api")
    return ""


def env():
    os.environ.get("ORDERS_HOST")
    os.environ["ORDERS_HOST"]
    os.getenv("ORDERS_HOST")


def durable(session, table):
    session.commit()
    table.insert()
    table.update()
    table.delete()
    table.select()
    session.query(Order)


def background():
    threading.Thread(target=env).start()
    BackgroundScheduler()


@app.task
def celery_job():
    pass


@shared_task
def shared_job():
    pass


# FastAPI verbs beyond get/post.
@app.put("/orders/<oid>")
def replace_order(oid):
    pass


@app.delete("/orders/<oid>")
def drop_order(oid):
    pass


@app.patch("/orders/<oid>")
def patch_order(oid):
    pass


# Django: the URL table, the ORM, and settings.
from django.conf import settings
from django.urls import path, re_path


urlpatterns = [
    path("orders/", list_orders),
    re_path(r"^orders/(?P<oid>\d+)/$", get_order),
    url(r"^legacy/$", list_orders),
]
router.register(r"orders", OrderViewSet)


def django_orm(Order, order, serializer):
    Order.objects.filter(status="new")
    Order.objects.get(pk=1)
    Order.objects.all()
    Order.objects.first()
    Order.objects.count()
    Order.objects.exists()
    Order.objects.select_related("customer")
    Order.objects.prefetch_related("lines")
    Order.objects.create(status="new")
    Order.objects.bulk_create([])
    Order.objects.update(status="done")
    Order.objects.get_or_create(pk=1)
    Order.objects.update_or_create(pk=1)
    order.save()
    order.delete()
    return settings.ORDERS_BACKEND
