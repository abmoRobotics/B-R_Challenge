'use strict'
const setTimeoutP = require('timers/promises').setTimeout;
const MAIN = require('../enum/main.json');
const CMD = require('../enum/commands.json');
const MQT = require('../enum/mqttenum.json');

/**
 * A station is a place on the board where a shuttle can be processed. It is configured in the beginning
 * of the board creation and is either in use or not. The station will also have an x,y coordinate on a 
 * 2 dimensional plane giving the position of the station. The station can be in four different states
 * NOT IN USE, IDLE, LOCKED, PROCESSING. 
 * When NOT IN USE it will be portrayed in gray on the HMI and a shuttle can just pass through it without 
 * using it.
 * When IDLE the station will hold the station color (as defined by the stationType). Here a new shuttle can
 * enter the station and begin processing.
 * When LOCKED, a shuttle is on the way to the station (or finished processing but not moved out yet) and no
 * other shuttle will be able to lock the station. Sort of like a semaphore so only one shuttle at the time
 * can move to a station.
 * When PROCESSING the shuttle is immediately on/under the station and the station will turn red, to display
 * that it is busy. The shuttle should not be able to move away from the station until the processing is done.
 */
module.exports = class Station {
    /**
     * 
     * @param {Function} notify notify function
     * @param {String} id id of the station
     * @param {Object} stationType 
     * @param {String} stationType.color color of the station
     * @param {Number} stationType.time timeout/processing time of station
     * @param {Boolean} inuse 
     * @param {Boolean} locked 
     * @param {Number} x 
     * @param {Number} y 
     */
    constructor(notify, id, stationType, inuse, locked, x, y) {
        this.notify = notify;
        this.id = id;
        this.stationType = stationType;
        this.locked = locked;
        this.utilization = 0;
        this.position = {
            x: x,
            y: y
        }
        this.state = (inuse) ? MAIN.STATE_IDLE : MAIN.NOT_IN_USE;
    }

    getId = () => {
        return this.id;
    };

    getStationType = () => {
        return this.stationType;
    }

    getPosition = () => {
        return this.position;
    }

    getLocked = () => {
        return this.locked;
    }

    setLocked = (locked) => {
        this.locked = locked;
    }

    lockStation = () => {
        this.setLocked(true);
    }

    unlockStation = () => {
        this.setLocked(false);
    }

    getState = () => {
        return this.state;
    };
    setState = (state) => {
        this.state = state;
    }

    /**
     * 
     * @param {Shuttle} shuttle 
     * @returns null
     */
    setProcessing = async (shuttleId) => {
        //Check if this station is in use, if not just return
        if (this.getState() === MAIN.NOT_IN_USE) return;
        //Store the time to aggregate utilization
        this.startTime = Date.now();
        //Set the state to processing
        this.setState(MAIN.STATE_PROCESSING);
        //Set the processing color (normally red)
        this.stationType.setColor(MAIN.PROCESSING_COLOR);
        //Notify user that this station is processing
        this.notify(MQT.TOPIC_STATUS, CMD.PROCESSING, { stationId: this.getId(), color: this.stationType.getColor(), shuttleId: shuttleId });
        //Set a timeout to simulate the process
        await setTimeoutP(this.stationType.getProcessingTime())
    }

    setIdle = (shuttleId) => {
        //Check if this station is in use, if not just return
        if (this.getState() === MAIN.NOT_IN_USE) return;
        //Set state to idle
        this.setState(MAIN.STATE_IDLE);
        //Increment the utilization time
        this.utilization += (Date.now() - this.startTime);
        //Reset the color of the station
        this.stationType.setColor(this.stationType.getOrgColor());
        //Notify user
        this.notify(MQT.TOPIC_STATUS, CMD.PROCESSING_DONE, { stationId: this.getId(), color: this.stationType.getColor(), shuttleId: shuttleId });
    }

    isProcessIdle = () => {
        if (this.getState() === MAIN.NOT_IN_USE) return true;
        return this.getState() === MAIN.STATE_IDLE;
    }

    getUtilization = () => {
        return this.utilization;
    };
};