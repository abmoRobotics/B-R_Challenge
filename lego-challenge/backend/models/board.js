'use strict'
const _ = require('lodash');
const Order = require("./order");
const Shuttle = require("./shuttle");
const Station = require("./station");
const StationType = require("./stationType");
const ERRORS = require('../enum/errors.json');
const MAIN = require('../enum/main.json');
const CMD = require('../enum/commands.json');
const MQT = require('../enum/mqttenum.json');
const Semaphore = require('./semaphore');
const setTimeoutP = require('timers/promises').setTimeout;


const PRINT = false;
const printOnId = undefined

//WE need to communicate with ExOS in case there is no simulation present
let ExosComm;
if (!MAIN.SIMULATION) {
    ExosComm = require('../controllers/exos_comm');
}


/**
 * The board is the main part of the program. It will define the board with all stations and shuttles on it.
 * The board is also responsible for moving a shuttle to and from a station. The board will recieve the commands
 * from the user and execute these. If a command is not possible it will throw and error for the user. The board 
 * is also responsible for moving a shuttle back to the starting position again once the shuttle has been moved
 * into the _dumping lane_ (where the products are dumped). The board will also keep track of which shuttles are
 * where and if a shuttle can or cannot move somewhere. It will also create a queue for the shuttles on the way
 * back so these do not collide. The board furthermore also keeps track of the time it takes for all orders to
 * be completed and will summarise this plus the utilization for each active station so that the students can 
 * use these numbers to optimize their ML-code.
 */
module.exports = class Board {
    constructor(id) {
        this.id = id;
        this.rows = 0;
        this.columns = 0;
        this.startingTime = 0;
        this.stations = {};
        this.orders = {};
        this.shuttles = {};
        this.queueingLane = [];
        this.shuttleReturnLaneStart;
        this.shuttleReturnLaneEnd;
        this.notifier = null;
        if (!MAIN.SIMULATION) this.exos_comm = new ExosComm();
    }

    storeNotifier(notifier, mqtt_client) {
        this.notifier = notifier;
        this.mqtt_client = mqtt_client;
    }

    /**
     * This resets the board to the 
     */
    resetBoard = () => {
        this.id = '';
        this.rows = 0;
        this.columns = 0;
        this.startingTime = 0;
        this.stations = {};
        this.orders = {};
        this.shuttles = {};
        this.queueingLane = [];
        this.startingLane = [];
    }

    /**
     * 
     * @param {Object} config configuration of the board
     * @param {Integer} config.rows number of rows on the board
     * @param {Integer} config.columns number of columns on the board
     * @param {Object[]} config.stations array of objects describing the stations
     * @param {String} config.stations.color color describing the color of the station
     * @param {String} config.stations.time processing time describing the timeout of the station
     * @param {Boolean} config.stations.inuse flag to describe the usage of the station
     * @param {Object[]} config.shuttles array of objects describing the stations
     * @returns {Object} exported board
     */
    configureBoard = (config) => {
        this.resetBoard();

        this.rows = config.rows;
        this.columns = config.columns;
        for (let i = 0; i < this.rows; i++) {
            for (let j = 0; j < this.columns; j++) {
                var matrixPos = i * this.columns + j;
                let id = 'PS' + i + j;
                let stationData = config.stations[matrixPos];
                let stationType = new StationType(stationData.inuse ? stationData.color : 'grey', stationData.time);
                let y = this.rows - i;
                let x = j;
                // let y = i + 1, x = j;
                this.stations[id] = new Station(this.notify.bind(this), id, stationType, stationData.inuse, false, x, y);
            }
        }

        //Add Dump lane
        this.rows += 1;
        for (let j = 0; j < this.columns; j++) {
            let id = 'ProductDumpLane_0' + j;
            let stationType = new StationType('grey', 0);
            this.stations[id] = new Station(this.notify.bind(this), id, stationType, false, false, j, this.rows);
        }

        //Add starting positions
        this.rows += 1;
        for (let j = 0; j < this.columns; j++) {
            let id = 'Start_0' + j;
            let stationType = new StationType('grey', 0);
            this.stations[id] = new Station(this.notify.bind(this), id, stationType, false, true, j, 0);
        }

        //Add shuttle return swim lane
        this.columns += 1;
        for (let j = 0; j < this.rows; j++) {
            let id = 'ShuttleReturnLane_' + j + (this.columns - 1);
            let stationType = new StationType('grey', 0);
            this.stations[id] = new Station(this.notify.bind(this), id, stationType, false, false, (this.columns - 1), j);
            if (j === 0) this.shuttleReturnLaneStart = id;
            if (j === (this.rows - 1)) this.shuttleReturnLaneEnd = id;
        }

        config.shuttles.forEach((shuttle, idx) => {
            //The starting station for each shuttle has to be calculated.
            //The first x will fit in the starting row,
            //and the remain y will fit into the ReturnLane
            let startingStation = 'Start_0' + idx;
            let x = idx, y = 0;
            if (idx >= (this.columns - 1)) {
                startingStation = 'ShuttleReturnLane_' + (idx - (this.columns - 1)) + (this.columns - 1);
                x = (this.columns - 1);
                y = (idx - (this.columns - 1));
                // console.log(startingStation);
                var station = this.stations[startingStation];
                station.lockStation();
                this.queueingLane.push(shuttle.id);
            }
            this.shuttles[shuttle.id] = new Shuttle(this.notify.bind(this), shuttle.id, x, y, startingStation, this.exos_comm);
        },this)

        // We will need a semaphore when moving the shuttles
        this.semaphore = new Semaphore(config.shuttles.length)
        let items = 0;
        config.orders.forEach(order => {
            let recipeItems = 0;
            order.recipe.map(recipe => { recipeItems += recipe.quantity});
            items += (order.quantity * recipeItems);
            this.orders[order.id] = new Order(this.notify.bind(this), order)
        }, this);

        this.totalItems = items;

        let board = this.exportBoard();
        this.notify(MQT.TOPIC_STATUS, 'CONF', board);
        this.updateOrderData();
        return board;
    }

    /**
     * Exports the board for the students and the HMI to get a snapshot of the simulation
     * @returns {Board}
     */
    exportBoard = () => {
        var return_board = {
            columns: this.columns,
            rows: this.rows,
            colors: ['green', 'yellow', 'blue'],
            stations: Object.values(this.stations).map(station => {
                return {
                    id: station.getId(),
                    position: station.getPosition(),
                    stationType: {
                        color: station.stationType.getColor(),
                        time: station.stationType.getProcessingTime(),
                    },
                    state: station.getState(),
                    locked: station.getLocked()
                }
            }),
            shuttles: Object.values(this.shuttles).map(shuttle => {
                return {
                    id: shuttle.getId(),
                    position: shuttle.getPosition(),
                    currentStation: shuttle.getCurrentStation(),
                    currentMix: shuttle.getCurrentMix(),
                    finishedStations: shuttle.getFinishedStations(),
                    mixDone: shuttle.getMixDone()
                }
            }),
            orders: Object.values(this.orders).map(order => {
                return {
                    id: order.getId(),
                    recipe: order.getRecipe(),
                    quantity: order.getQuantity(),
                    done: order.getDone()
                }
            })
        }
        return return_board;
    }

    notify(topic, method, data) {

        if (this.notifier !== null) {
            let mess = {
                method: method,
                data: data
            };
            this.mqtt_client.publish(topic, JSON.stringify(mess));
            this.notifier.send(MAIN.BOARD_ID, mess);

            try {
                let board = this.exportBoard();
                this.mqtt_client.publish(MQT.TOPIC_BOARD, JSON.stringify(board));
            } catch (error) {
                throw error;
            }

        }
    }

    startingProcess = () => {
        //Check if game has been started
        if (this.startingTime === 0) {
            //If it hasnt, set it to current time
            this.startingTime = Date.now();
            //Notify user that process has started - clock is ticking
            this.notify(MQT.TOPIC_STATUS, CMD.MIX_STARTED, { startTime: this.startingTime, endTime: 0 });
        }
    }
    endingProcess = () => {
        //Get the time
        const endTime = Date.now();
        //Calculate the total time of the game
        let totalTime = endTime - this.startingTime, sumStationUtilz = 0;
        let utils = {}, avgUtil = 0, totalStations = 0;
        //Penalize unused stations
        let a = 0.6, STATION_NOT_USED = 100;
        Object.values(this.stations).map(station => {
            //Skip all empty stations - transportation lanes
            if (station.getState() === MAIN.NOT_IN_USE) return;
            //Get a stations utilization
            let util = station.getUtilization();
            // divide the utilization with total time and store for a given station
            let utilztime = (util / totalTime)
            utils[station.getId()] = utilztime;
            //If utilization time is 0 penalise the station hard as this would be equivalent to wasted money
            if (utilztime === 0) {
                sumStationUtilz += STATION_NOT_USED;
            } else {
                //Otherwise add a weight to the sum
                sumStationUtilz += (a / utilztime);
            }
            avgUtil += utilztime; 
            totalStations++;
        });

        avgUtil /= totalStations;
        //Calculate the b-weight as
        let b = 1 - a;
        let robotCellCost = 100;
        //Use the time score formula according to the paper
        let timeScore = (b*totalTime / this.totalItems) + sumStationUtilz;
        let timeScoreCell = totalStations*robotCellCost + timeScore;
        console.log('time score (part 1)', timeScore, 'total items', this.totalItems);
        console.log('time score (part 2)', timeScoreCell, 'total items', this.totalItems);
        //Update the user that we've ended the carousel
        this.notify(MQT.TOPIC_STATUS, CMD.MIX_ENDED, { startTime: this.startingTime, endTime: endTime, averageUtilization: avgUtil, utilizationPerStation: utils, timeScore: timeScore, timeScoreCellCost: timeScoreCell });
    }

    /**
     * Moves a shuttle to a station, can only move the shuttle if the station is finished and the semaphore
     * has been cleared, otherwise error is thrown
     * @param {String} shuttleId the id of the shuttle we want to move on the board
     * @param {String} stationId the id of the station to which we want to move the shuttle
     */
    moveShuttle = async (shuttleId, stationId) => {
        try {
            //Get a shuttle
            let shuttle = this.shuttles[shuttleId];
            //If no shuttle is found, throw an error
            if (!shuttle) throw new Error('No shuttle found with id ' + shuttleId, { cause: ERRORS.NO_SHUTTLE_FOUND });
            //Set the new starting station (where the user wants to move the shuttle)
            shuttle.setStartingStation(stationId);

            //If the shuttle is already set, request a new mix
            if (shuttle.getCurrentStation() === stationId) {
                // shuttle.resetMix();
                this.notify(MQT.TOPIC_STATUS, CMD.REQUEST_NEW_MIX, { shuttleId, shuttleId });
            } else {
                // If the shuttle hasnt reached the starting station, evaluate how far the shuttle can move
                let startingStation = await this.evaluateStartingBlock(shuttle); 
                if (startingStation) {
                    //Remove the shuttle from the queueing lane, as the shuttle now is in the starting lane
                    this.freeUpQueueingLane(shuttleId);
                    //Push the id to array for later
                    this.startingLane.push(shuttleId);
                    //Get the current station the shuttle is in (which should be in the starting lane)
                    let returnLaneStation = this.stations[shuttle.getCurrentStation()];
                    //Unlock the precious station
                    returnLaneStation.unlockStation();
                    //Lock the new starting lane station
                    startingStation.lockStation();
                    //move the shuttle as far as possible
                    await shuttle.moveOnReturn(startingStation.getId(), startingStation.getPosition(), null, this.shuttles);
                    //TODO: remove timeout and exchange for handshake
                    if (!MAIN.SIMULATION) await setTimeoutP(1000);
                    //Move all stations in the return lane
                    await this.moveStationsInReturnLane();
                    //If our shuttle now moved to the starting station
                    if (shuttle.getCurrentStation() === stationId) {
                        //request a new mix and move teh user along
                        this.notify(MQT.TOPIC_STATUS, CMD.REQUEST_NEW_MIX, { shuttleId, shuttleId })
                    } else {
                        // else throw an error and the let user know they need to make this call again
                        throw new Error('Shuttle ' + shuttleId + ' has not reached designated starting station', { cause: { errorId: ERRORS.SHUTTLE_HAS_NOT_REACHED_STARTING_STATION, shuttleId: shuttleId, startLane: stationId }});    
                    }
                } else {
                    //If the new starting station is locked, user needs to repeatedly call it until shuttle can move
                    throw new Error('Start station ' + shuttleId + ' is still locked, cannot move to it', { cause: { errorId: ERRORS.START_STATION_LOCKED, shuttleId: shuttleId, startLane: stationId }});
                }
            } 

        } catch (err) {
            // console.log(err);
            throw(err);
        }
    }

    async moveShuttleInDirection(shuttleId, direction) {
        //Find the shuttle
        let shuttle = this.shuttles[shuttleId];

        //If no shuttle is found throw error
        if (!shuttle) throw new Error('No shuttle found with id ' + shuttleId, { cause: { errorId: ERRORS.NO_SHUTTLE_FOUND, shuttleId: shuttleId, direction: direction }});
        //If the shuttle is in the Dumping or Return Lane we cannot control the shuttle and thus throw an error
        if (shuttle.getCurrentStation().includes('Dump') || shuttle.getCurrentStation().includes('Return')) throw new Error('Shuttle outside of movable scope', { cause: { errorId: ERRORS.SHUTTLE_NOT_IN_MOVABLE_SCOPE, shuttleId: shuttleId, direction: direction }});
        //If no mix is asigned to the shuttle throw an error
        if (shuttle.getCurrentMix() === '') throw new Error('No mix assigned to shuttle with id ' + shuttleId, { cause: { errorId: ERRORS.NO_MIX_ASSIGNED_TO_SHUTTLE, shuttleId: shuttleId, direction: direction }});

        //Get the station the shuttle currently is at
        let station = this.stations[shuttle.getCurrentStation()], position, newPosition;
        //Check if we found a station
        if (station) {
            //If the station is not idle (i.e. still executing) we need to throw an error
            if (!station.isProcessIdle()) throw new Error('Processing Station ' + station.getId() + ' has not finished yet', { cause: { errorId: ERRORS.STATION_STILL_PROCESSING, shuttleId: shuttleId , direction: direction}});
            //If the station is idle, retrieve the position
            position = station.getPosition();
        } else {
            //If no station is found, the shuttle is in the starting position
            position = this.stations[shuttle.getStartingStation()].getPosition();
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
            default: throw new Error('Invalid direction command sent: ' + direction + '. Please refer to commands: forth, back, right or left. Or shorthand format f, l, r, b.', { cause: { errorId: ERRORS.INVALID_SHUTTLE_MOVE_COMMAND, shuttleId: shuttleId, direction: direction }});
        }

        //Check if the new position is still on the board, if not throw an error
        if (newPosition.x < 0 || newPosition.y < 0 || newPosition.x >= (this.columns - 1) || newPosition.y > (this.rows - 1)) {
            throw new Error('Trying to reach position outside of board', { cause: { errorId: ERRORS.SHUTTLE_OUT_OF_BOUNDS, shuttleId: shuttleId, direction: direction }});
        }

        //Find the new station
        let newStation;
        Object.values(this.stations).map(station => {
            let position = station.getPosition();
            if (position.x === newPosition.x && position.y === newPosition.y) {
                newStation = station;
            }
        });

        //If the new station is locked, throw an error
        if (newStation.getLocked()) throw new Error('Processing Station ' + newStation.getId() + ' is still locked, cannot move to it', { cause: { errorId: ERRORS.STATION_LOCKED, shuttleId: shuttleId, direction: direction }});
        //Check if the new station is part of the dumplane
        if (newStation.getId().includes('DumpLane')) {
            //If so retrieve the end return lane station
            let srls = this.stations[this.shuttleReturnLaneEnd];
            if (srls.getLocked()) {
                //If the station is locked, throw an error
                throw new Error ('Return Station is locked, wait to free up to move shuttle into dumping lane', { cause: { errorId: ERRORS.STATION_LOCKED, shuttleId: shuttleId }});
            } else {
                //If not, lock teh station
                srls.lockStation();
            }

        }
        //then lock the new station
        newStation.lockStation();
        // let currStation = this.stations[shuttle.getCurrentStation()];
        //Force the process to start, should be called everytime but will only execute code the first time
        this.startingProcess();
        //Move the shuttle
        await shuttle.move(newStation.getId(), newStation.getPosition(), ((newStation.getState() === MAIN.NOT_IN_USE) ? null : newStation.getStationType().color), !(newStation.getState() === MAIN.NOT_IN_USE), this.shuttles);
        //TODO: remove timeout and exchange for handshake
        if (!MAIN.SIMULATION) await setTimeoutP(1000);
        //Once the shuttle has moved away, unlock the old station so a new can use it
        station.unlockStation();
        //If the new station is in use start the processing
        if (newStation.getState() !== MAIN.NOT_IN_USE) {
            //Start the process of the station
            await newStation.setProcessing(shuttle.getId());
            //Once the process is done, reset the station to idle
            newStation.setIdle(shuttle.getId());
        }
        try {
            //Then check if the shuttle is in the dumplane
            await this.checkIfInDumpLane(shuttle);
            //And finally evaluate the return lane and see how much further up we can move all shuttles waiting
            await this.moveStationsInReturnLane();
        } catch (err) {
            if (PRINT || shuttleId === printOnId) console.log(err);
        }
    }

    /**
     * Sets a new mix to a shuttle if the previous mix is finished
     * @param {String} shuttleId the id of the shuttle we want to manipulate
     * @param {String} mixId the id of the mix we want to update the mix with
     */
    setShuttleMix = (shuttleId, mixId) => {
        //Retrieve the right shuttle
        let shuttle = this.shuttles[shuttleId];

        //If a shuttle is not found or the mix is nto done, we cannot update the shuttle and thus throw appropriate error
        if (!shuttle) throw new Error('No shuttle found', { cause: { errorId: ERRORS.NO_SHUTTLE_FOUND, shuttleId: shuttleId }});
        if (!shuttle.getMixDone()) throw new Error('Mix is not finished yet, cannot change mix', { cause: { errorId: ERRORS.MIX_IS_NOT_FINISHED, shuttleId: shuttleId }});
        //TODO: check that a mix actually exists before setting it to a shuttle, otherwise errors down the line...

        //Set the mix
        shuttle.setCurrentMix(mixId);
        //Once the mix is done we want to update the orders so the client knows how many orders of each exist
        Object.values(this.orders).map(order => {
            if (order.getId() === mixId) {
                order.setStarted();
            }
        });
        this.updateOrderData();
    }

    checkIfInDumpLane = async (shuttle) => {
        //First find out the current station of the shuttle
        let currStation = this.stations[shuttle.getCurrentStation()];
        //Check if the ID of the station includes the word Dumplane, then we are at the end
        if (currStation.getId().includes('DumpLane')) {
            //Running the real system we need to add some extra time for the communication etc, so we wait one second for things to catch up
            //TOOO: implement handshake instead
            if (!MAIN.SIMULATION) await setTimeoutP(1000)

            //Unlock the curreent station the shuttle is at
            currStation.unlockStation();

            //Evaluate the order to see if it is done or not
            await this.evaluateOrder(shuttle, true);

            //<Get the shuttle return lane station (srls)
            let srls = this.stations[this.shuttleReturnLaneEnd];
            // Move the shuttle in the return lane to the last station on the line
            await shuttle.moveOnReturn(this.shuttleReturnLaneEnd, srls.getPosition(),  null, this.shuttles);

            //TOOO: implement handshake instead of waiting
            await setTimeoutP(1000)

            //add the shuttle to the queue so we at later state can evaluate where the shuttle should move
            this.queueingLane.push(shuttle.getId());

            // We evaluate which station the shuttle is in the return queue. If the shuttle is at the 
            let returnLaneStation = await this.evaluateReturnBlock(shuttle);

            //If we get a return station, and this station is not the last one in the queue (then we cannot move)
            if (returnLaneStation && returnLaneStation.getId() !== srls.getId()) {

                //we unlock the endstation (srls)
                srls.unlockStation();

                // we lock the next available return lane station
                returnLaneStation.lockStation();

                //force a reset of the mix that the shuttle just finished
                shuttle.resetMix();

                //and finally move the shuttle to the newly locked return lane station
                await shuttle.moveOnReturn(returnLaneStation.getId(), returnLaneStation.getPosition(),  null, this.shuttles);

                //TOOO: implement handshake instead of waiting
                if (!MAIN.SIMULATION) await setTimeoutP(1000)

                //Only if we return to the bottom right corner are we allowed to move to our starting position
                // we inform the user that the shuttle is located at the beginning of the lane and they are now
                // once again responsible for the shuttle
                if (returnLaneStation.getId() === this.shuttleReturnLaneStart) {
                    this.notify( MQT.TOPIC_STATUS , CMD.SHUTTLE_AT_START, { shuttleId: shuttle.getId() });
                }
            }
        }
    }

    evaluateOrder = async (shuttle, print) => {
        //First get the current order from the shuttle
        let currOrder = this.getOrderFromShuttle(shuttle);
        //Get all the stations that the shuttle has passed/finished
        let finishedStations = shuttle.getFinishedStations(), colors = [];
        //Sort them by color (as the order could differ)
        finishedStations = _.sortBy(finishedStations, 'color');
        //Sort the recipe order according to color
        let recipe = _.sortBy(currOrder.recipe, 'color');
        //Compare the two arrays and see if we are finished
        let isFinished = _.isEqual(recipe, finishedStations);
        //Set if the shuttle is finished or not
        shuttle.setMixDone(isFinished);
        //If finished
        if (isFinished) {
            //Evaluate if the order is complete
            currOrder.orderCompleted();
            //Update client and front end with new data
            this.updateOrderData();
        }
    }


    /**
     * Will get the order that the current shuttle is working on
     * @param {Shuttle} shuttle 
     * @returns {Order}
     */
    getOrderFromShuttle = (shuttle) => {
        var mixId = shuttle.getCurrentMix();
        return this.orders[mixId];
    }

    updateOrderData = () => {
        let data = [], totalFinished = true;
        //Iterate over all orders and aggregate data
        Object.values(this.orders).map(order => {
            totalFinished &= order.evaluateOrder();
            data.push({
                id: order.getId(),
                started: order.getStarted(),
                quantity: order.getQuantity(),
                completed: order.getCompletedOrders()
            })
        })
        //Notify users
        this.notify(MQT.TOPIC_STATUS, CMD.ORDER_UPDATED, data);
        //this is just for testing
        this.orderData = data;
        // if user is finished, end the process
        if (totalFinished) this.endingProcess();
    }

    getOrderData = () => {
        //this is just for testing
        return this.orderData;
    }

    /**
     * evaluates which position we can move a shuttle to on the return lane,
     * in case there is a shuttle in the way or not
     * @param {Shuttle} shuttle 
     */
    evaluateReturnBlock = async (shuttle) => {
        //Get the y position for the shuttle (since we are moving down the column, column isn't interesting)
        let blockedAt;
        let y = shuttle.getPosition().y - 1;
        //Start at the end
        for (var j = y; j >= 0; j--) {
            let id = 'ShuttleReturnLane_' + j + (this.columns - 1);
            //Get the shuttle return lane station (srls)
            let srls = this.stations[id];
            //Check if station is locked
            if (srls.getLocked()) {
                //If the station is locked, we can move the shuttle to the previous station
                let prevStationId = 'ShuttleReturnLane_' + (j + 1) + (this.columns - 1);
                blockedAt = this.stations[prevStationId];
                break;
            }

            //if we are at the last station and it's not locked
            if (j === 0 && !srls.getLocked()) {
                blockedAt = this.stations[this.shuttleReturnLaneStart];
                break;
            }
        }
        return blockedAt;
    }

    /**
     * evaluates which position we can move a shuttle to on the starting lane,
     * in case there is a shuttle in the way or not
     * @param {Shuttle} shuttle 
     */
    evaluateStartingBlock = async (mainShuttle) => {
        //Get the current station
        let blockedAt, passedStartingStation = false, currStation = mainShuttle.getCurrentStation();
        //Get the starting station number
        let currStationNumber = currStation.split('Start_0')[1];
        //If the current station is the same as the shuttle starting station, do nothing
        if (mainShuttle.getStartingStation() !== currStation) {
            //Iterate over the columns, since we are moving across the row, the row itself isnt interesting
            for (var j = (this.columns - 2); j >= 0; j--) {
                if (j >= currStationNumber) continue;
                let id = 'Start_0' + j;
                //Get the starting lane station (sls)
                let sls = this.stations[id];
                //If the station isnt locked, we can go to this station
                if (!sls.getLocked() && !passedStartingStation ) {
                    blockedAt = sls;
                } else {
                    //If the station is locked, we cant go any further, previous station is stored
                    break;
                }
                //Make sure we dont pass the given station, could happen at a completely empty row, where we dont want to go to the first station
                passedStartingStation = mainShuttle.getStartingStation() === id;
            }
        }
        return blockedAt;
    }

    freeUpQueueingLane = (id) => {
        // FInd the index of the id in the queue and pop/slice it out
        let index = this.queueingLane.indexOf(id);
        if (index !== -1) this.queueingLane.splice(index, 1);
    }

    moveStationsInReturnLane = async () => {
        //Take a temporary copy of the queueing lane so we dont mess up the original
        let tempQueueingLane = JSON.parse(JSON.stringify(this.queueingLane));
        for (var j = 0; j < tempQueueingLane.length; j++) {
            let queuingShuttle = tempQueueingLane[j];
            //Get the selected shuttle in the queue
            let shuttle = this.shuttles[queuingShuttle], newStation;
            //Get the station the shuttle is currently located at, which we want to leave
            let prevStation = this.stations[shuttle.getCurrentStation()];
            //Chech if this station is the first station in the return lane
            if (shuttle.getCurrentStation() === this.shuttleReturnLaneStart) {
                //in this case do nothing and notify the user that the shuttle is at the start station
                this.notify( MQT.TOPIC_STATUS , CMD.SHUTTLE_AT_START, { shuttleId: shuttle.getId() });
            //If the shuttle is in the starting lane (which it shouldnt be here) - do nothing
            } else if (shuttle.getCurrentStation().includes('Start')) {
                // EVALUATE STARTING LANE
            } else {
                // And if none above, we are in the return lane. Evaluate where we can move the station
                newStation = await this.evaluateReturnBlock(shuttle);                
            }

            //If we in the above passage found a station, and this station is different from the current station,
            //it means we can move the shuttle (at least) one station onwards
            if (newStation && newStation.getId() !== shuttle.getCurrentStation()) {
                //Unlock the previous/current station
                prevStation.unlockStation();
                //And lock the next station
                newStation.lockStation();
                //Move the shuttle to the new station
                await shuttle.moveOnReturn(newStation.getId(), newStation.getPosition(),  null, this.shuttles);
            }
        }
    }
};