const express = require('express');
const app = express();
const router = express.Router();

app.get('/orders', (req, res) => res.send(process.env.ORDERS_HOST));
app.post('/orders', (req, res) => res.send(process.env['ORDERS_HOST']));
router.put('/orders/:id', (req, res) => res.send(''));
router.delete('/orders/:id', (req, res) => res.send(''));

const server = new grpc.Server();
server.addService(shopProto.OrderService.service, {});
