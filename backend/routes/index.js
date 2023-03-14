const express = require('express');
const router = express.Router();

const config_controller = require('../controllers/configuration');
const CMD = require('../enum/commands.json');
const MQT = require('../enum/mqttenum.json');

module.exports = (webSocketNotifier, mqtt_client) => {

    mqtt_client.on('message', async function (topic, message) {
        if (topic == MQT.TOPIC_COMMAND) {
            // message is Buffer
            // exmaples:
            //
            // MOVE_SHUTTLE_TO: mosquitto_pub.exe -t "aws_br" -m "{\"method\": \"MOVE_SHUTTLE_TO\", \"id\": \"2\", \"direction\": \"f\"}"
            //
            //SET_SHUTTLE_MIX: mosquitto_pub.exe -t "aws_br" -m "{\"method\": \"SET_SHUTTLE_MIX\", \"id\": 0, \"mixId\": \"Mix A\"}"
            try {
                let data = await message.toString();
                // console.log(data)
                data = JSON.parse(data);

                try {
                    switch (data.method) {
                        case CMD.SET_CONF:
                            await config_controller.set_up_configuration_api(data.data, webSocketNotifier, mqtt_client);
                            break;
                        case CMD.MOVE_SHUTTLE_TO:
                            await config_controller.move_shuttle_in_direction(data.id, data.direction);
                            break;
                        case CMD.SET_SHUTTLE_MIX:
                            await config_controller.set_shuttle_mix(data.id, data.mixId);
                            break;
                        case CMD.MOVE_SHUTTLE_TO_START:
                            await config_controller.move_shuttle_to_station(data.id, data.stationId);
                            break;
                        default: console.log(MQT.TOPIC_COMMAND, 'no command found, default', data.method); break;//mqtt_client.publish('aws_br/fail', JSON.stringify({ success: false, message: data.method + ' did not exist!'})); break;
                    }
                } catch (err) {
                    let id = data.id || 'No id';
                    let mess = {
                        method: CMD.FAILED,
                        failedMethod: data.method,
                        id: id,
                        error: err.cause,
                        message: err.message
                    }
                    mqtt_client.publish(MQT.TOPIC_STATUS, JSON.stringify(mess));
                }
            } catch (err) {
                let mess = {
                    method: CMD.FAILED,
                    data: 'Invalid JSON string'
                }
                mqtt_client.publish(MQT.TOPIC_STATUS, JSON.stringify(mess));
                console.log(MQT.TOPIC_COMMAND, 'command failed', err); //mqtt_client.publish('aws_br/fail', JSON.stringify({ success: false, message: data.method + ' did not exist!'})); break;
            }
        }

    });


    router.post('/config', async (req, res, next) => {
        try {
            let config = req.body.data;

            let board = await config_controller.set_up_configuration_api(config, webSocketNotifier, mqtt_client);
            // webSocketNotifier.send('2001', board);
            res.status(200).json({ success: true, board: board });
        } catch (err) {
            console.log(err);
            res.status(500).json({ success: false, message: err.message })
        }
    });

    router.delete('/config', async (req, res, next) => {
        try {
            await config_controller.dispose();
            res.status(200).json({ success: true });
        } catch (err) {
            console.log(err);
            res.status(500).json({ success: false, message: err.message })
        }
    });

    router.post('/shuttle/move/:id/:direction', async (req, res, next) => {
        try {
            let { id, direction } = req.params;
            console.log('move triggered', id, direction)
            await config_controller.move_shuttle_in_direction(id, direction);
            res.status(200).json({ success: true });
        } catch (err) {
            console.log(err);
            res.status(500).json({ success: false, message: err.message })
        }
    });


    router.post('/shuttle/move/:id/to/:stationId', async (req, res, next) => {
        try {
            let { id, stationId } = req.params;
            let board = await config_controller.move_shuttle_to_station(id, stationId);
            res.status(200).json({ success: true, board, board });
        } catch (err) {
            console.log(err);
            res.status(500).json({ success: false, message: err.message })
        }
    });
    router.get('/shuttle/:id/set/mix/:mixId', async (req, res, next) => {
        try {
            let { id, mixId } = req.params;
            await config_controller.set_shuttle_mix(id, mixId);
            res.status(200).json({ success: true });
        } catch (err) {
            console.log(err);
            res.status(500).json({ success: false, message: err.message })
        }
    });

    router.post('/move/shuttle/:id/to/start/pos/:startPos', async (req, res, next) => {
        try {
            let { id, startPos } = req.params;
            await config_controller.move_shuttle_to_station(id, startPos);
            res.status(200).json({ success: true });
        } catch (err) {
            console.log(err);
            res.status(500).json({ success: false, message: err.message })
        }
    });

    router.get('/config', async (req, res, next) => {
        try {

            let board = await config_controller.get_config();
            // webSocketNotifier.send('2001', board);
            res.status(200).json({ success: true, board: board });
        } catch (err) {
            console.log(err);
            res.status(500).json({ success: false, message: err.message })
        }
    });

    return router;
};