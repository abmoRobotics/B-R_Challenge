'use strict'
const _ = require('lodash');
const setTimeoutP = require('timers/promises').setTimeout;
const MAIN = require('../enum/main.json');
const CMD = require('../enum/commands.json');
const MQT = require( '../enum/mqttenum.json' );
const ERRORS = require('../enum/errors.json');

const TRY_AGAIN_TIMEOUT = (MAIN.HEADLESS) ? 0 : 200;
const RETURN_MOVING_TIME = (MAIN.HEADLESS) ? 0 : MAIN.RETURN_MOVING_TIME;
const MOVING_TIME  = (MAIN.HEADLESS) ? 0 : MAIN.MOVING_TIME;
const QUICK_EVALUATION_OF_RETURN_LANE = true;

/**
 * A Shuttle is an object (on the 6D it will be an actual magnetic shuttle moving) that moves across the board.
 * A shuttle can move one step forward, backwards, right or left at the time. A shuttle will recieve a mix it is
 * supposed to complete before exiting the board. A shuttle will have a starting position where it starts and where
 * it will return to once the shuttle goes off into the boards dumping lane. The shuttle will always keep track of
 * which station it currently is at. The shuttle cannot move diagonally or multiple steps at once.
 */
module.exports = class Shuttle {
    constructor (board, notify, id, x, y, startingStation, exos_comm) {
        this.notify = notify;
        this.board = board;
        this.id = id;
        this.position = {
            x: x,
            y: y
        };
        this.currentStation = startingStation;
        this.startingStation = startingStation;
        //Lock this station
        this.board.stations[this.currentStation].lockStation();
        this.currentMix = ''; // we might not have to care, if we have independent mix orders for each mix and we just check at the end of the day what mix it is
        this.finishedStations = [];
        this.mixStarted = false;
        this.mixDone = false;
        this.moving = false;
        this.busy = false;
        this.stopped = false;
        this.exos_comm = exos_comm;
        this.triggerHandoverToClient();
        this.triggerInitialReturnLaneMovement();
    };

    getId = () => {
        return this.id;
    };

    setCurrentStation = (station) => {
        this.currentStation = station;
    };

    getCurrentStation = () => {
        return this.currentStation;
    };

    setCurrentMix = (mix) => {
        this.currentMix = mix;
        // this.notify( MQT.TOPIC_STATUS , CMD.MIX_SET, { shuttleId: this.getId() });
    };

    getCurrentMix = () => {
        return this.currentMix;
    };

    setPosition = (pos) => {
        this.position = pos;
    };

    getPosition = () => {
        return this.position;
    };

    stop = () => {
        this.stopped = true;
    };

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
    };

    getFinishedStations = () => {
        return this.finishedStations;
    };

    setMixDone = (done) => {
        this.mixDone = done;
    };

    getMixDone = () => {
        // console.log(this.id, this.currentMix, 'mix started', this.mixStarted, 'mix done', this.mixDone);
        return !this.mixStarted || (this.mixStarted && this.mixDone);
    };

    resetMix = () => {
        this.finishedStations = [];
        this.mixDone = false;
        this.mixStarted = false;
        this.currentMix = '';
    };

    /**
     * 
     * @param {String} direction the direction the shuttle should travel in
     * @returns {String} name of the new stationId
     */
    async move (direction) {
        let prevStationId = this.getCurrentStation();
        let movingObj = this._move(direction);
        //First set mix started to true, so we can keep track of it
        this.mixStarted = true;
        //If the color exists (i.e. we are on a station)
        if (movingObj.color !== null) this.addFinishedStation(movingObj.color);
        //Store current station id, position and set moving to true
        this.currentStation = movingObj.newStationId;
        this.position = movingObj.newStationPos;
        this.moving = true;
        //Notify user the shuttle is moving
        this.notify( MQT.TOPIC_STATUS , CMD.MOVE, { shuttleId: this.getId(), newStationId: movingObj.newStationId, position: movingObj.newStationPos });
        //Send moving command to 6D or simulate it with a timeout
        if (MAIN.SIMULATION) {
            await setTimeoutP(MOVING_TIME);
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
        this.notify( MQT.TOPIC_STATUS , CMD.MOVE_DONE, { shuttleId: this.getId(), stationId: movingObj.newStationId, inuse: movingObj.newStationId.includes('DumpLane') ? null : movingObj.inuse });
        //reset moving flag
        this.moving = false;
        //Once the shuttle has moved away, unlock the old station so a new can use it
        this.board.stations[prevStationId].unlockStation();

        return movingObj.newStationId;
    };

    setBusy = (busy) => {
        this.busy = busy;
    }

    getBusy = () => {
        return this.busy;
    }

    /**
     * 
     * @param {String} stationId the id of the station
     * @param {Object} position position of the new station
     * @param {Integer} position.x x position of the new station
     * @param {Integer} position.y y position of the new station
     */
    async moveOnReturn (stationId, position, inuse) {
        //First set mix started to true, so we can keep track of it
        this.moving = true;
        // if (parseInt(this.getId()) > 9) console.log('moving',this.getId(),'on return to',stationId);
        //Store current station id, position and set moving to true
        this.currentStation = stationId;
        this.position = position;
        //Only to notify the front end that we are moving the shuttle
        //DO NOT SEND MOVE_DONE command as it is not triggered by the client 
        this.notify( MQT.TOPIC_STATUS , CMD.MOVE, { shuttleId: this.getId(), newStationId: stationId, position: position });
        
        if (MAIN.SIMULATION) {
            await setTimeoutP(RETURN_MOVING_TIME);
        } else {
            console.log(new Date().toISOString(), 'sending positions to exos, moveOnReturn, shuttle', this.getId(), 'position', position)
            let movePromise = this.exos_comm.setData(this.getId(), this.board.shuttles);
            this.exos_comm.sendData();
            await movePromise;
        }
        //Notify user that the move is done
        // this.notify( MQT.TOPIC_STATUS , CMD.MOVE_DONE, { shuttleId: this.getId(), stationId: stationId, inuse: (inuse !== undefined) ? inuse : null });
        //reset moving flag
        this.moving = false;
    };

    _move (direction) {
        //If the shuttle is in the Dumping or Return Lane we cannot control the shuttle and thus throw an error
        if (this.getCurrentStation().includes('Dump') || this.getCurrentStation().includes('Return')) 
            throw new Error('Shuttle outside of movable scope', { cause: { errorId: ERRORS.SHUTTLE_NOT_IN_MOVABLE_SCOPE, shuttleId: this.getId(), direction: direction }});
        //If no mix is asigned to the shuttle throw an error
        if (this.getCurrentMix() === '') 
            throw new Error('No mix assigned to shuttle with id ' + this.getId(), { cause: { errorId: ERRORS.NO_MIX_ASSIGNED_TO_SHUTTLE, shuttleId: this.getId(), direction: direction }});

        //Get the station the shuttle currently is at
        let station = this.board.stations[this.getCurrentStation()], position, newPosition;
        //Check if we found a station
        if (station) {
            //If the station is not idle (i.e. still executing) we need to throw an error
            if (!station.isProcessIdle()) 
                throw new Error('Processing Station ' + station.getId() + ' has not finished yet', { 
                    cause: { 
                        errorId: ERRORS.STATION_STILL_PROCESSING, 
                        shuttleId: this.getId(), 
                        direction: direction
                    }
                });
            //If the station is idle, retrieve the position
            position = station.getPosition();
        } else {
            //If no station is found, the shuttle is in the starting position
            position = this.board.stations[this.getStartingStation()].getPosition();
        }

        //move shuttle accordingly
        switch (direction) {
            case 'l':
            case 'left':
                newPosition = {
                    x: position.x - 1,
                    y: position.y
                }
                break;
            case 'f':
            case 'forward':
            case 'forth':
                newPosition = {
                    x: position.x,
                    y: position.y + 1
                }
                break;
            case 'b':
            case 'back':
                newPosition = {
                    x: position.x,
                    y: position.y - 1
                }
                break;
            case 'r':
            case 'right':
                newPosition = {
                    x: position.x + 1,
                    y: position.y
                }
                break;
            default: throw new Error('Invalid direction command sent: ' + direction + '. Please refer to commands: forth (forward), back, right or left. Or shorthand format f, l, r, b.', 
                { cause: { 
                    errorId: ERRORS.INVALID_SHUTTLE_MOVE_COMMAND, 
                    shuttleId: this.getId(), 
                    direction: direction 
                }
            });
        }

        //Check if the new position is still on the board, if not throw an error
        if (newPosition.x < 0 || newPosition.y < 0 || newPosition.x >= (this.columns - 1) || newPosition.y > (this.rows - 1)) {
            throw new Error('Trying to reach position outside of board', { cause: { errorId: ERRORS.SHUTTLE_OUT_OF_BOUNDS, shuttleId: this.getId(), direction: direction }});
        }

        //Find the new station
        let newStation;
        Object.values(this.board.stations).map(station => {
            let position = station.getPosition();
            if (position.x === newPosition.x && position.y === newPosition.y) {
                newStation = station;
            }
        });

        //If the new station is locked, throw an error
        if (newStation.getLocked()) throw new Error('Processing Station ' + newStation.getId() + ' is still locked, cannot move to it', { 
            cause: { 
                errorId: ERRORS.STATION_LOCKED, 
                shuttleId: this.getId(), 
                direction: direction 
            }
        });
        //Check if the new station is part of the dumplane
        // if (newStation.getId().includes('DumpLane')) {
        //     //If so retrieve the end return lane station
        //     let srls = this.board.stations[this.board.getShuttleReturnLaneEnd()];
        //     //TODO: Trigger internal movement to handoverplace
        //     if (srls.getLocked()) {
        //         //If the station is locked, throw an error
        //         throw new Error ('Return Station is locked, wait to free up to move shuttle into dumping lane', { cause: { errorId: ERRORS.STATION_LOCKED, shuttleId: this.getId() }});
        //     } else {
        //         //If not, lock teh station
        //         srls.lockStation();
        //     }

        // }
        //then lock the new station
        newStation.lockStation();
        // let currStation = this.stations[shuttle.getCurrentStation()];
        //Force the process to start, should be called everytime but will only execute code the first time
        this.board.startingProcess();
        return {
            newStationId: newStation.getId(), 
            newStationPos: newStation.getPosition(), 
            color: ((newStation.getState() === MAIN.NOT_IN_USE) ? null : newStation.getStationType().color), 
            inuse: !(newStation.getState() === MAIN.NOT_IN_USE)
        }
    };

    moveToStartingStation = () => {
        let shuttle = this;
        setTimeout(async () => {
            let shuttleAtStation = shuttle.evaluateStartingBlock();
            // console.log('Moving to start station for shuttle', shuttle.getId())
            if (!shuttleAtStation) {
                if (!this.stopped) shuttle.moveToStartingStation(); //This might be a bad solution
            } else {
                let currentStation = shuttle.board.stations[shuttle.getCurrentStation()];
                // console.log('Moving to start station', shuttleAtStation.getId(), 'for shuttle', shuttle.getId(), 'starting station', shuttle.getStartingStation())
                if (shuttle.getCurrentStation() === shuttle.getStartingStation()) {
                    // console.log('Moving to start station', shuttleAtStation.getId(), 'for shuttle', shuttle.getId(), 'triggered reached - 1')
                    shuttle.notify(MQT.TOPIC_STATUS, CMD.REQUEST_NEW_MIX, { shuttleId: shuttle.getId() });
                    currentStation.unlockStation();
                } else {
                    await shuttle.moveOnReturn(shuttleAtStation.getId(), shuttleAtStation.getPosition(), false);
                    currentStation.unlockStation();
                    shuttleAtStation.lockStation();
                    if (shuttle.getCurrentStation() === shuttle.getStartingStation()) {
                        // console.log('Moving to start station', shuttleAtStation.getId(), 'for shuttle', shuttle.getId(), 'triggered reached - 2')
                        shuttle.notify(MQT.TOPIC_STATUS, CMD.REQUEST_NEW_MIX, { shuttleId: shuttle.getId() });
                        currentStation.unlockStation();
                    } else {
                        // console.log('Moving to start station', shuttleAtStation.getId(), 'for shuttle', shuttle.getId(), 'retesting')
                        if (!this.stopped) shuttle.moveToStartingStation();
                    }
                }
            }
        }, TRY_AGAIN_TIMEOUT);
    };

    /**
     * evaluates which position we can move a shuttle to on the starting lane,
     * in case there is a shuttle in the way or not
     * @param {Shuttle} shuttle 
     */
    evaluateStartingBlock = () => {
        //Get the current station
        let blockedAt, passedStartingStation = false, currStationId = this.getCurrentStation();
        //Get the starting station number
        let currStationNumber = this.board.stations[currStationId].getPosition().x;
        //If the current station is the same as the shuttle starting station, do nothing
        if (this.getStartingStation() !== currStationId) {
            //Iterate over the columns, since we are moving across the row, the row itself isnt interesting
            for (var j = (this.board.columns - 2); j >= 0; j--) {
                if (j >= currStationNumber) continue;
                let id = 'Start_0' + j;
                //Get the starting lane station (sls)
                let sls = this.board.stations[id];
                //If the station isnt locked, we can go to this station
                if (!sls.getLocked() && !passedStartingStation ) {
                    blockedAt = sls;
                } else {
                    //If the station is locked, we cant go any further, previous station is stored
                    break;
                }
                //Make sure we dont pass the given station, could happen at a completely empty row, where we dont want to go to the first station
                passedStartingStation = this.getStartingStation() === id;
            }
        }
        return blockedAt;
    };

    getMoving = () => {
        return this.moving;
    };

    setStartingStation = (station) => {
        this.startingStation = station;
    };

    getStartingStation = () => {
        return this.startingStation;
    };

    triggerHandoverToClient = () => {
        if (this.getCurrentStation() === this.board.getShuttleReturnLaneStart()) {
            // console.log('trigger handover at start')
            this.notify( MQT.TOPIC_STATUS , CMD.SHUTTLE_AT_START, { shuttleId: this.getId() });
        }
    };

    triggerInitialReturnLaneMovement = () => {
        if (this.getCurrentStation().includes('ShuttleReturnLane') && !(this.getCurrentStation() === this.board.getShuttleReturnLaneStart())) {
            this.moveInReturnLane();   
        }
    };

    moveToReturnLane = async () => {
        let endLaneStation = this.board.stations[this.board.getShuttleReturnLaneEnd()];
        let currentStation = this.board.stations[this.getCurrentStation()];
        await this.moveOnReturn(endLaneStation.getId(), endLaneStation.getPosition(), false);
        currentStation.unlockStation();
        this.moveInReturnLane();
    };

    moveInReturnLane = () => {
        let shuttle = this;
        setTimeout(async () => {
            // console.log('triggered interval, moving shuttle in return lane', this.getId());
            let stationInReturnLane = shuttle.evaluateReturnBlock();
            if (!stationInReturnLane) {
                this.moveInReturnLane();
            } else {
                let currentStation = shuttle.board.stations[shuttle.getCurrentStation()];
                // console.log('moving shuttle', shuttle.getId(), 'at return lane between', shuttle.getCurrentStation(), 'and', shuttle.board.getShuttleReturnLaneStart())
                if (shuttle.getCurrentStation() === shuttle.board.getShuttleReturnLaneStart()) {
                    // console.log('sending shuttle at start cmd - 1 - shuttle', shuttle.getId())
                    shuttle.notify( MQT.TOPIC_STATUS , CMD.SHUTTLE_AT_START, { shuttleId: shuttle.getId() });
                } else {

                    if (!stationInReturnLane.getLocked()) {
                        stationInReturnLane.lockStation();
                        currentStation.unlockStation();
                        await shuttle.moveOnReturn(stationInReturnLane.getId(), stationInReturnLane.getPosition(), false);
                    }
                    
                    if (shuttle.getCurrentStation() === shuttle.board.getShuttleReturnLaneStart()) {
                        // console.log('sending shuttle at start cmd - 2 - shuttle', shuttle.getId())
                        shuttle.notify( MQT.TOPIC_STATUS , CMD.SHUTTLE_AT_START, { shuttleId: shuttle.getId() });
                        // clearInterval(shuttle.returnLaneStationFunc);
                    } else {
                        if (!this.stopped) shuttle.moveInReturnLane();
                    }
                }
            }
        }, TRY_AGAIN_TIMEOUT);
    };

    /**
     * evaluates which position we can move a shuttle to on the return lane,
     * in case there is a shuttle in the way or not
     * @param {Shuttle} shuttle 
     */
    evaluateReturnBlock = () => {
        //Get the y position for the shuttle (since we are moving down the column, column isn't interesting)
        let blockedAt;
        let y = this.getPosition().y - 1;
        //Start at the end
        if (QUICK_EVALUATION_OF_RETURN_LANE) {
            for (var j = y; j >= 0; j--) {
                let id = 'ShuttleReturnLane_' + j + (this.board.columns - 1);
                //Get the shuttle return lane station (srls)
                let srls = this.board.stations[id];
                // console.log('check for shuttle',this.getId(),'if srls', id, 'is locked',srls.getLocked())
                //Check if station is locked
                if (srls.getLocked()) {
                    //If the station is locked, we can move the shuttle to the previous station
                    let prevStationId = 'ShuttleReturnLane_' + (j + 1) + (this.board.columns - 1);
                    // console.log('We return station', prevStationId, 'for',this.getId())
                    blockedAt = this.board.stations[prevStationId];
                    break;
                }
    
                //if we are at the last station and it's not locked
                if (j === 0 && !srls.getLocked()) {
                    blockedAt = this.board.stations[this.board.getShuttleReturnLaneStart()];
                    break;
                }
            }
        } else {
            let id = 'ShuttleReturnLane_' + y + (this.board.columns - 1);
            let srls = this.board.stations[id];
            if (!srls.getLocked()) {
                blockedAt = srls;
            }

            //if we are at the last station and it's not locked
            if (j === 0) {
                srls = this.board.stations[this.board.getShuttleReturnLaneStart()];
                if (!srls.getLocked()) blockedAt = srls;
            }
        }
        return blockedAt;
    };



    moveInDumpLane = () => {
        let shuttle = this;
        setTimeout(async () => {
            // console.log('triggered interval, moving shuttle in return lane', this.getId());
            let stationInDumpLane = shuttle.evaluateDumpingLane();
            if (!stationInDumpLane) {
                if (!this.stopped) shuttle.moveInDumpLane();
            } else {
                let currentStation = shuttle.board.stations[shuttle.getCurrentStation()];
                if (!stationInDumpLane.getLocked()) {
                    stationInDumpLane.lockStation();
                    await shuttle.moveOnReturn(stationInDumpLane.getId(), stationInDumpLane.getPosition(), false);
                }
                currentStation.unlockStation();
                
                if (shuttle.getCurrentStation() === shuttle.board.getShuttleReturnLaneEnd()) {
                    setTimeout(() => {
                        shuttle.moveInReturnLane();
                    }, TRY_AGAIN_TIMEOUT);
                } else {
                    if (!this.stopped) shuttle.moveInDumpLane();
                }
            }
        }, TRY_AGAIN_TIMEOUT);
    };


    /**
     * evaluates which position we can move a shuttle to on the return lane,
     * in case there is a shuttle in the way or not
     * @param {Shuttle} shuttle 
     */
    evaluateDumpingLane = () => {
        //Get the y position for the shuttle (since we are moving down the column, column isn't interesting)
        let blockedAt;
        let y = this.getPosition().x;
        var j = y + 1;
        //Start at the end
        if (j < (this.board.columns - 1)) {
            let id = 'ProductDumpLane_0' + j;
            let srls = this.board.stations[id];
            if (!srls.getLocked()) {
                blockedAt = srls;
            }
        } else {
            let srls = this.board.stations[this.board.getShuttleReturnLaneEnd()];
            if (!srls.getLocked()) blockedAt = srls;
        }
        return blockedAt;
    };

};