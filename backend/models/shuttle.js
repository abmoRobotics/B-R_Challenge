'use strict'
const _ = require('lodash');
const setTimeoutP = require('timers/promises').setTimeout;
const MAIN = require('../enum/main.json');
const CMD = require('../enum/commands.json');
const MQT = require( '../enum/mqttenum.json' );

/**
 * A Shuttle is an object (on the 6D it will be an actual magnetic shuttle moving) that moves across the board.
 * A shuttle can move one step forward, backwards, right or left at the time. A shuttle will recieve a mix it is
 * supposed to complete before exiting the board. A shuttle will have a starting position where it starts and where
 * it will return to once the shuttle goes off into the boards dumping lane. The shuttle will always keep track of
 * which station it currently is at. The shuttle cannot move diagonally or multiple steps at once.
 */
module.exports = class Shuttle {
    constructor (notify, id, x, y, startingStation, exos_comm) {
        this.notify = notify;
               
        this.id = id;
        this.position = {
            x: x,
            y: y
        };
        this.currentStation = startingStation;
        this.startingStation = startingStation;
        this.currentMix = ''; // we might not have to care, if we have independent mix orders for each mix and we just check at the end of the day what mix it is
        this.finishedStations = [];
        this.mixStarted = false;
        this.mixDone = false;
        this.moving = false;
        this.exos_comm = exos_comm;
    }
    getId = () => {
        return this.id;
    };

    setCurrentStation = (station) => {
        this.currentStation = station;
    }

    getCurrentStation = () => {
        return this.currentStation;
    }

    setCurrentMix = (mix) => {
        this.currentMix = mix;
        // this.notify( MQT.TOPIC_STATUS , CMD.MIX_SET, { shuttleId: this.getId() });
    }

    getCurrentMix = () => {
        return this.currentMix;
    }

    setPosition = (pos) => {
        this.position = pos;
    }

    getPosition = () => {
        return this.position;
    }

    /**
     * This function iterates over all finished stations and if it founds the same station
     * it updates the quantity, otherwise pushes the new value to the array
     * @param {String} color the color of the station
     */
    addFinishedStation = (color) => {
        let colorFound = false;
        this.finishedStations.forEach(finishedStation => {
            if (finishedStation.color === color) {
                colorFound = true;
                finishedStation.quantity++;
            }
        });
        if (!colorFound) this.finishedStations.push({color: color, quantity: 1});
    }

    getFinishedStations = () => {
        return this.finishedStations;
    }

    setMixDone  = (done) => {
        this.mixDone = done;
    }

    getMixDone = () => {
        // console.log(this.id, this.currentMix, 'mix started', this.mixStarted, 'mix done', this.mixDone);
        return !this.mixStarted || (this.mixStarted && this.mixDone);
    }

    resetMix = () => {
        this.finishedStations = [];
        this.mixDone = false;
        this.mixStarted = false;
        this.currentMix = '';
    }

    /**
     * 
     * @param {String} stationId the id of the station
     * @param {Object} position position of the new station
     * @param {Integer} position.x x position of the new station
     * @param {Integer} position.y y position of the new station
     * @param {String} color processing color of the new station
     * @param {Boolean} inuse will tell use if a station is in use or not
     */
    async move (stationId, position, color, inuse, shuttles) {
        //First set mix started to true, so we can keep track of it
        this.mixStarted = true;
        //If the color exists (i.e. we are on a station)
        if (color !== null) this.addFinishedStation(color);
        //Store current station id, position and set moving to true
        this.currentStation = stationId;
        this.position = position;
        this.moving = true;
        //Notify user the shuttle is moving
        this.notify( MQT.TOPIC_STATUS , CMD.MOVE, { shuttleId: this.getId(), newStationId: stationId, position: position });
        //Send moving command to 6D or simulate it with a timeout
        if (MAIN.SIMULATION) {
            await setTimeoutP(MAIN.MOVING_TIME);
        } else {
            try {
                let movePromise = this.exos_comm.setData(this.getId(), shuttles);
                this.exos_comm.sendData();
                await movePromise;
            } catch (err) {
                console.log('shuttle move function failing', err)
            }
        }
        //Notify user that the move is done
        this.notify( MQT.TOPIC_STATUS , CMD.MOVE_DONE, { shuttleId: this.getId(), stationId: stationId, inuse: stationId.includes('DumpLane') ? null : inuse });
        //reset moving flag
        this.moving = false;
    }

    /**
     * 
     * @param {String} stationId the id of the station
     * @param {Object} position position of the new station
     * @param {Integer} position.x x position of the new station
     * @param {Integer} position.y y position of the new station
     */
    async moveOnReturn (stationId, position, inuse, shuttles) {
        //First set mix started to true, so we can keep track of it
        this.moving = true;
        //Store current station id, position and set moving to true
        this.currentStation = stationId;
        this.position = position;
        //Notify user the shuttle is moving
        this.notify( MQT.TOPIC_STATUS , CMD.MOVE, { shuttleId: this.getId(), newStationId: stationId, position: position });
        let MOVING_TIME = (stationId.includes('ShuttleReturnLane')) ? MAIN.RETURN_MOVING_TIME : MAIN.MOVING_TIME;
        if (MAIN.SIMULATION) {
            await setTimeoutP(MAIN.RETURN_MOVING_TIME);
        } else {
            console.log(new Date().toISOString(), 'sending positions to exos, moveOnReturn, shuttle', this.getId(), 'position', position)
            let movePromise = this.exos_comm.setData(this.getId(), shuttles);
            this.exos_comm.sendData();
            await movePromise;
        }
        //Notify user that the move is done
        this.notify( MQT.TOPIC_STATUS , CMD.MOVE_DONE, { shuttleId: this.getId(), stationId: stationId, inuse: (inuse !== undefined) ? inuse : null });
        //reset moving flag
        this.moving = false;
    }

    getMoving = () => {
        return this.moving;
    }

    setStartingStation = (station) => {
        this.startingStation = station;
    }

    getStartingStation = () => {
        return this.startingStation;
    }
};