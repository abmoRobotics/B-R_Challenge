const setTimeoutP = require('timers/promises').setTimeout;
const board = require('../data/board.feed.data.json');
const MQT = require('../../../backend/enum/mqttenum.json'); //Use MQT not MQTT to avoid naming conflicts.
const CMD = require('../../../backend/enum/commands.json');
const model = require('./model');
const RETRY_TIMEOUT = 2000;  //milliseconds
const PRINT = false;

let client, once = 0, finished_orders = {};

exports.setup = (mqtt_client) => {
    client = mqtt_client;
}

exports.set_current_board_status = (board) => {
    this.board = board;
}

exports.send_data = async (telegram) => {
    // publishes the data telegram to the mqtt
    
    await setTimeoutP(1000)
    await client.publish(MQT.TOPIC_COMMAND, JSON.stringify(telegram));
}

exports.initialize = async () => {
    // sends initial telegram that sets everything up
    // reads this from the board.feed.data.json
    let init_telegram = { "method": "SET_CONF", "type": "POST", "data": board }
    await this.send_data(init_telegram);
}

exports.switch_status = async (telegram) => {
    
    await setTimeoutP(1000)

    switch (telegram.method) {
        case CMD.ORDER_UPDATED:
            //When the order data is updated we can keep track on what needs to be done
            finished_orders = telegram.data;
            break;
        case CMD.CONF:
            //First get initial mixes and set all shuttles to these
            let mixes = model.get_initial_mixes(board.columns);
            mixes.forEach(mix => {
                let mix_telegram = { "method": "SET_SHUTTLE_MIX", "id": mix.shuttleId, "mixId": mix.mixId }
                
                this.send_data(mix_telegram);
            }, this)
            
            //Then send first move for all shuttles
            let moves = model.get_inital_moves(board.columns);
            moves.forEach(async move => {
                let move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": move.shuttleId, "direction": move.move }
                this.send_data(move_telegram);
            }, this)
            break;

        case CMD.MOVE_DONE:
            //When a move is finished, we want to get the next move. But only if station which the shuttle
            //lands on isnt in use, in that case we have to wait for the processing done telegram
            if (telegram.data.inuse === false) {
                let dir = model.get_next_move(telegram.data.shuttleId);
                if (dir !== undefined) {
                    let move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": telegram.data.shuttleId, "direction": dir }
                    this.send_data(move_telegram);
                }
            }
            break;

        case CMD.PROCESSING_DONE:
            //Sent when the processing of station is finished, and the shuttle can be moved on again
            let dir = model.get_next_move(telegram.data.shuttleId);
            if (dir !== undefined) {
                let move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": telegram.data.shuttleId, "direction": dir }
                this.send_data(move_telegram);
            }
            break;

        case CMD.FAILED:
            //In the case of an error, if the telegram contains an errorId we can handle it, else just print
            //the error
            if (telegram?.error?.errorId) {
                // If the target station is locked (20001) or still processing (20002) keep sending the same telegram
                // over and over again untill the desired station is free
                if (telegram?.error?.errorId == 20001 || telegram?.error?.errorId == 20002) {
                    let dir = model.get_current_move(telegram.error.shuttleId);
                    if (dir !== undefined) {
                        await setTimeoutP(RETRY_TIMEOUT)
                        let move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": telegram.error.shuttleId, "direction": dir }
                        this.send_data(move_telegram);
                    }
                } else if (telegram?.error?.errorId == 20003) {
                    //If the start station is locked (20003) send the same move command again
                    await setTimeoutP(RETRY_TIMEOUT) 
                    let move_telegram = { "method": "MOVE_SHUTTLE_TO_START", "id": telegram.error.shuttleId, "stationId": telegram.error.startLane }
                    this.send_data(move_telegram);
                } else if (telegram?.error?.errorId == 10007) {
                    //If the shuttle hasnt reached the start station yet (10007) send the same move command again
                    await setTimeoutP(RETRY_TIMEOUT)
                    let move_telegram = { "method": "MOVE_SHUTTLE_TO_START", "id": telegram.error.shuttleId, "stationId": telegram.error.startLane }
                    this.send_data(move_telegram);
                } else if (telegram?.error?.errorId == 10006) {
                    //If the shuttle is trying to move outside of the scope of the board, do somethingm else
                    await setTimeoutP(RETRY_TIMEOUT)
                    let dir = model.get_current_move(telegram.error.shuttleId);
                    // if (dir === 'l') dir = 'r';
                    // if (dir === 'r') dir = 'l';
                    let move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": telegram.error.shuttleId, "direction": dir }
                    this.send_data(move_telegram);
                }
            } else {
                if (PRINT) console.log('Strange things arrived', telegram)
            }

            break;
        case CMD.MIX_ENDED:
            //When the mix has ended, print data and exit the process. Optimize the code
            console.log('total time', (telegram.data.endTime - telegram.data.startTime) / 1000, 's', 'avg utilisation', telegram.data.averageUtilization, 'stationwise utilisation', telegram.data.utilizationPerStation)
            console.log('Please optimise avg and stationwise utilisation first and then total time, your time score is:',telegram.data.timeScore)
            process.exit(0);

        case CMD.SHUTTLE_AT_START:
            
            let move_telegram, startStation, mix;
            // A potentially unncessary check, but make sure the shuttle is reset on local side aswell before proceeding 
            if (model.is_move_reset(telegram.data.shuttleId)) {

                // Here we start the returning of shuttles
                //First off, check if we are finished: i.e. all mixes have shuttles asigned to them
                let weAreFinished = areWeFinished();

                if (!weAreFinished) {
                    //If we are finished
                    //get the next mix
                    mix = model.get_next_mix(finished_orders, telegram.data.shuttleId);
                    //build telegram and send
                    let mix_telegram = { "method": "SET_SHUTTLE_MIX", "id": telegram.data.shuttleId, "mixId": mix }
                    this.send_data(mix_telegram);
                    //if a mix is returned - i.e. something is left to gather, we build the name of the start station and set next movement.
                    if (mix !== undefined) {
                        let newStartStation = model.get_start_station(mix);
                        startStation= ('Start_0'+ newStartStation.start)
                        model.set_next_movement(telegram.data.shuttleId, mix, newStartStation);
                    }
                }
                if (weAreFinished) {
                    //If we are finished, we only want to move the shuttle to a start station and do nothing else
                    startStation = 'Start_0' + (once);
                    console.log('moving to start station', startStation)
                    //Make sure we only update the once variable the number of columns we have
                    if (once < this.board.columns) once++;
                }

                move_telegram = { "method": "MOVE_SHUTTLE_TO_START", "id": telegram.data.shuttleId, "stationId": startStation }

                //If we have a move telegram we send it
                if (!!move_telegram) {
                    this.send_data(move_telegram);
                }
            }
            break;

        case CMD.REQUEST_NEW_MIX:
            //Naming convesion here is a bit off, we could see it as a start for the shuttle to move out on the board
            let firstMoveDir = model.get_next_move(telegram.data.shuttleId)
            let next_move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": telegram.data.shuttleId, "direction": firstMoveDir }
            this.send_data(next_move_telegram);
            break;
    }
}

function areWeFinished() {
    //iterate over all orders and compare quantity to started to see if we need to send more 
    //shuttles or not
    let totalQuantity = 0, totalStarted = 0;
    Object.values(finished_orders).map(order => {
        totalQuantity += order.quantity;
        totalStarted += order.started;
    })
    // console.log('Evaluating quantities', totalQuantity, 'and finished', totalStarted)
    return totalQuantity === totalStarted;
}