'use strict'

const MAIN = require('../enum/main.json');
module.exports = class StationType {
    /**
     * Station type
     * @param {String} color color of the station
     * @param {Number} time timeout/processing time of station
     */
    constructor (color, time) {
        this.color = color;
        this.orgColor = color;
        this.time = (MAIN.HEADLESS) ? 0 : time;
    }

    getColor = () => {
        return this.color;
    };

    setColor = (color) => {
        this.color = color;
    }

    getOrgColor = () => {
        return this.orgColor;
    };

    getProcessingTime = () => {
        return this.time * 1000;
    }
}