const express = require('express');
const cors = require('cors');
const NotifierService = require("./controllers/notifier.js");
const notifier = new NotifierService();
const swaggerUi = require('swagger-ui-express'),
    swaggerDocument = require('./swagger.json');

const MQT = require('./enum/mqttenum.json'); //Use MQT not MQTT to avoid naming conflicts.
const mqtt = require('mqtt');
const mqtt_client = mqtt.connect(MQT.BROKER_PATH);


require('dotenv').config();

const routes = require('./routes/index');

const app = express();
const port = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

const server = app.listen(port, () => {
    console.log(`Server is running on port: ${port}`);
});
notifier.connect(server);              // and connected here in app.js

mqtt_client.on('connect', function () {

    //Create AND/OR publish topic 
    mqtt_client.publish(MQT.TOPIC_COMMAND, "Backend connected");
    mqtt_client.publish(MQT.TOPIC_STATUS, "Backend connected");
    mqtt_client.publish(MQT.TOPIC_BOARD, "Backend connected");


    mqtt_client.subscribe(MQT.TOPIC_COMMAND, function (err) {
        if (err) console.log('CLIENT CANNOT SUBSCRIBE TO COMMAND TOPIC')
    });
});

app.use('/', routes(notifier, mqtt_client));
app.use(
    '/api-docs',
    swaggerUi.serve,
    swaggerUi.setup(swaggerDocument)
);

return server;