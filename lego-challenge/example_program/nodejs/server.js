const MQT = require('../../backend/enum/mqttenum.json'); //Use MQT not MQTT to avoid naming conflicts.
console.log('MQTT Client started, trying to connect to', MQT.BROKER_PATH)
const main = require('./controllers/main');

const mqtt = require('mqtt');
const mqtt_client = mqtt.connect(MQT.BROKER_PATH);
main.setup(mqtt_client);

mqtt_client.on('connect', function () {
    console.log('connecting')

    //Create AND/OR publish topic 
    mqtt_client.publish(MQT.TOPIC_COMMAND, "Student program connected");
    mqtt_client.publish(MQT.TOPIC_STATUS, "Student program connected");
    mqtt_client.publish(MQT.TOPIC_BOARD, "Student program connected");


    mqtt_client.subscribe(MQT.TOPIC_STATUS, async (err) => {
        if (err) {
            console.log('STUDENT CLIENT CANNOT SUBSCRIBE TO COMMAND TOPIC')
        } else {
            await main.initialize();
        }
    });

    mqtt_client.subscribe(MQT.TOPIC_BOARD, async (err) => {
        if (err) console.log('STUDENT CLIENT CANNOT SUBSCRIBE TO COMMAND TOPIC')
    });
});

mqtt_client.on('message', async (topic, message) => {
    try {
        let data = await message.toString();
        data = JSON.parse(data);
        switch (topic) {
            case MQT.TOPIC_BOARD: 
                // console.log('BOARD RECIEVED', data);
                main.set_current_board_status(data)
                break;
    
            case MQT.TOPIC_STATUS: 
                // console.log('STATUS', data);
                main.switch_status(data);
                break;
    
            default: console.log('not handled', topic); break;
        }
    } catch (err) {
        console.log('Error from message', err);
    }
});

mqtt_client.on('close', function () {
    console.log('Connection closed')
});

mqtt_client.on('error', function (err) {
    if (err) console.log('Connection error', err)
});

mqtt_client.on('offline', function () {
    console.log('MQTT server offline')
});

let callAmount = 0;
process.on('SIGINT', function() {
    if(callAmount < 1) {
        console.log(`✅ The server has been stopped - closing connection`);
        mqtt_client.end();
    }

    callAmount++;
});
