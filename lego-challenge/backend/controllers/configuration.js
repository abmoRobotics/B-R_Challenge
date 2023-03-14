'use strict'
let Board = require('../models/board');

let board = new Board('board1');

exports.set_up_configuration_api = async (config, webSocketNotifier, mqtt_client) => {
    try {
        return await this.set_up_configuration(config, webSocketNotifier, mqtt_client);
    } catch (err) {
        throw (err);
    }
};

exports.set_up_configuration = async (config, webSocketNotifier, mqtt_client) => {
    board.storeNotifier(webSocketNotifier, mqtt_client);
    return await board.configureBoard(config);

    // console.log('setup configuration', board)
};

exports.get_config = async () => {
    return await board.exportBoard();
}

exports.move_shuttle_to_station = async (id, stationId) => {
    try {
        return await board.moveShuttle(id, stationId);
    } catch (e) {
        throw (e);
    }
};

exports.move_shuttle_in_direction = async (id, direction) => {
    try {
        return await board.moveShuttleInDirection(id, direction);
    } catch (e) {
        throw (e);
    }
};
exports.set_shuttle_mix = async (id, mixId) => {
    try {
        return await board.setShuttleMix(id, mixId);
    } catch (e) {
        throw (e);
    }
}


exports.dispose = () => {
    board.resetBoard();
};