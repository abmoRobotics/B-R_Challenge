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
    };

    getShuttleReturnLaneStart = () => {
        return this.shuttleReturnLaneStart;
    };

    getShuttleReturnLaneEnd = () => {
        return this.shuttleReturnLaneEnd;
    };


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
                let id = 'PS' + (this.rows - i) + (this.columns - j);
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
        this.updateOrderData();

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
            this.shuttles[shuttle.id] = new Shuttle(this, this.notify.bind(this), shuttle.id, x, y, startingStation, this.exos_comm);
        },this)

        let board = this.exportBoard();
        this.notify(MQT.TOPIC_STATUS, 'CONF', board);
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
        console.log('time score', timeScore, 'total items', this.totalItems);
        //Update the user that we've ended the carousel
        this.notify(MQT.TOPIC_STATUS, CMD.MIX_ENDED, { startTime: this.startingTime, endTime: endTime, averageUtilization: avgUtil, utilizationPerStation: utils, timeScore: timeScore, timeScoreCellCost: timeScoreCell });

        //Cancel all shuttles trying to move
        Object.values(this.shuttles).map(shuttle => {
            shuttle.stop();
        });

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
            shuttle.moveToStartingStation();

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
        if (shuttle.getBusy()) throw new Error('Shuttle busy', { cause: ERRORS.SHUTTLE_BUSY_WITH_CMD });
        shuttle.setBusy(true);
        try {
            // if (parseInt(shuttleId) > 8) console.log('move shuttle', shuttleId, '1 step',direction)
            let newStationId = await shuttle.move(direction);
            let newStation = this.stations[newStationId];
            
            //If the new station is in use start the processing
            if (newStation.getState() !== MAIN.NOT_IN_USE) {
                //Start the process of the station
                await newStation.setProcessing(shuttle.getId());
                //Once the process is done, reset the station to idle
                newStation.setIdle(shuttle.getId());
            }
    
            if (newStationId.includes('DumpLane')) {
                shuttle.moveInDumpLane();
                this.evaluateOrder(shuttle);
                shuttle.resetMix();
            }
            shuttle.setBusy(false)
        } catch (err) {
            shuttle.setBusy(false);
            throw err;
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
        } else {
            console.log('Shuttle',shuttle.getId(), 'not completed order', currOrder.getId(),'but finished, stations it has passed', finishedStations,'stations it should have passed', recipe)
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


    freeUpQueueingLane = (id) => {
        // FInd the index of the id in the queue and pop/slice it out
        let index = this.queueingLane.indexOf(id);
        if (index !== -1) this.queueingLane.splice(index, 1);
    }

    isStationLocked = (stationId) => {
        let station = this.stations[stationId];
        return station.getLocked();
    };
};