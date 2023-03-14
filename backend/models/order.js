'use strict'

const MAIN = require('../enum/main.json');

// id: 'Mix B',
// quantity: 6,
// recipe: [{
//     color: "blue",
//     quantity: 1
// },{
//     color: "yellow",
//     quantity: 1
// }]

/**
 * The order defines which reciepes and in what quantities it should be filled.
 * Once a shuttle has finihsed a mix, the completed order will be increased. When
 * the number of completed orders matches the order quantity the order is finished.
 */
module.exports = class Order {
    /**
     * 
     * @param {Function} notify notiy callback function
     * @param {Object} order order object
     * @param {String} order.id the id of the order
     * @param {Number} order.quantity the quantity of the order
     * @param {Object[]} order.recipe a list of the recipes in an order
     * @param {String} order.recipe.color the color of the recipe
     * @param {Number} order.recipe.quantity the quantity of the recipe in order to fill the order
     * 
     */
    constructor (notify, order) {
        this.notify = notify;
        this.id = order.id;
        this.quantity = order.quantity;
        this.started = 0;
        this.completedOrders = 0;
        this.recipe = order.recipe;
        this.done = false
    }

    getId = () => {
        return this.id;
    }

    getQuantity = () => {
        return this.quantity;
    }

    getRecipe = () => {
        return this.recipe;
    }

    getDone = () => {
        return this.done;
    }

    setStarted = () => {
        this.started++;
    }

    getStarted = () => {
        return this.started;
    }

    getCompletedOrders = () => {
        return this.completedOrders;
    }

    orderCompleted = () => {
        this.completedOrders++;
    }

    evaluateOrder = () => {
        // If the number of orders equal to the number of completed orders, the order is done
        this.done = (this.completedOrders === this.quantity);
        return this.done;
    }

};