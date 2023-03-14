
const movements = require('../data/board.movements.json');
const shuttles = require('../data/board.shuttles.json');

exports.get_initial_mixes = (columns) => {
    //TODO: Implement your own method
    let mixes = [];
    for (var j = 0; j < columns; j++) {
        let shuttle = shuttles[j];
        // console.log(movements)
        try {
            shuttle.movements = movements[shuttle.currentMix][j][0].instr;
            shuttle.intialMixSet = true;
        } catch (err) {
            shuttle.movements = []
        }
        mixes.push({
            shuttleId: shuttle.shuttleId,
            mixId: shuttle.currentMix
        })
    }
    return mixes;
};

exports.get_next_mix = (finished_orders, shuttleId) => {
    //TODO: Implement your own method
    //map upp orders

    let mix;
    for (var j = 0; j < finished_orders.length; j++){
        let order = finished_orders[j];
        if (order.started < order.quantity) {
            mix = order.id;
            break;
        }
    }
    shuttles.forEach(shuttle => {
        if (shuttle.shuttleId === shuttleId) {
            shuttle.currentMovePos = -1;
            shuttle.currentMix = mix;
        }
    });
    console.log('get next mix for shuttle id', shuttleId, finished_orders, 'resulting in chosen mix:', mix);
    // if (mix === undefined) console.log(mixId);
    return mix;
};

exports.get_current_mix = (shuttleId) => {
    //TODO: Implement your own method
    let mix;
    shuttles.forEach(shuttle => {
        if (shuttle.shuttleId === shuttleId) {
            mix = shuttle.currentMix;
            console.log('get current mix', mix, 'for shuttle',shuttleId)
        }
    });
    return mix;
};

exports.get_inital_moves = (columns) => {
    //TODO: Implement your own method
    let moves = [];
    for (var j = 0; j < columns; j++) {
        let shuttle = shuttles[j];
        shuttle.currentMovePos++;
        // console.log(movement.shuttleId, movement.currentMix)
        moves.push({
            shuttleId: shuttle.shuttleId,
            move: shuttle.movements[shuttle.currentMovePos]
        })
    }
    return moves;
};

exports.get_next_move = (shuttleId) => {
    //TODO: Implement your own method
    let dir;
    shuttles.forEach(shuttle => {
        if (shuttle.shuttleId === shuttleId && shuttle.currentMix !== '' && shuttle.currentMix !== undefined) {
            shuttle.currentMovePos++;
            // console.log(movement.currentMix, movement[movement.currentMix], shuttleId)
            try {
                dir = shuttle.movements[shuttle.currentMovePos]; 
                if (!dir) console.log(shuttleId, shuttle.currentMix, shuttle.movements, shuttle.currentMovePos)
            } catch (err) {
                console.log('get_next_move, error for shuttle:', shuttleId, 'mix: ', shuttle.currentMix, 'movement pos', shuttle.currentMovePos, 'err as', err)
            }

        }
    })
    return dir;
};

exports.get_current_move = (shuttleId) => {
    //TODO: Implement your own method
    let dir;
    shuttles.forEach(shuttle => {
        if (shuttle.shuttleId === shuttleId && shuttle.currentMix !== '' && shuttle.currentMix !== undefined) {
            try {
                dir = shuttle.movements[shuttle.currentMovePos];
                
                if (!dir) console.log(shuttleId, shuttle.currentMix, shuttle.movements, shuttle.currentMovePos)
            } catch (err) {
                console.log('get_current_move, error for shuttle:', shuttleId, 'mix: ', shuttle.currentMix, 'movement pos', shuttle.currentMovePos, 'err as', err)
            }
        }
    })
    return dir;
}

exports.is_move_reset = (shuttleId) => {
    //TODO: Implement your own method
    let isMoveReset = false;
    shuttles.forEach(shuttle => {
        if (shuttle.shuttleId === shuttleId) {
            isMoveReset = shuttle.currentMovePos !== -1 || !shuttle.intialMixSet;
        }
    });
    return isMoveReset;
};

exports.get_start_station = (mixId) => {
    //TODO: Implement your own method
    //incorporate which starting positions
    let optimalCost = Number.MAX_SAFE_INTEGER, optimalStartingPos, optimalPos;
    // console.log(mixId, movements[mixId])
    for (const [startingPos, startingData] of Object.entries(movements[mixId])) {
        for (const [idx, movementData] of Object.entries(startingData)) {
            if (optimalCost > movementData.cost) {
                optimalCost = movementData.cost;
                optimalPos = idx;
                optimalStartingPos = startingPos;
            }
        }
    }
    console.log('new mix', mixId, 'chosen at starting col', optimalStartingPos, 'with new path', optimalPos, 'given cost', optimalCost)

    // we pick the new starting pos at random
    // let arrayOfPossibleStartingPositions = Object.keys(movements[mixId]);
    // let randomStartingPos = Math.floor(Math.random() * arrayOfPossibleStartingPositions.length);
    // console.log('random starting pos', randomStartingPos, arrayOfPossibleStartingPositions[randomStartingPos]);
    // let randomPathPos = Math.floor(Math.random() * Object.entries(movements[mixId][arrayOfPossibleStartingPositions[randomStartingPos]]).length);
    // console.log('random path pos', randomPathPos)
    // let movementData = movements[mixId][arrayOfPossibleStartingPositions[randomStartingPos]][randomPathPos]
    // optimalCost = movementData.cost;
    // optimalPos = randomPathPos;
    // optimalStartingPos = arrayOfPossibleStartingPositions[randomStartingPos];
    return { 'cost': optimalCost, 'pos': optimalPos, 'start': optimalStartingPos };
};

exports.set_next_movement = (shuttleId, mixId, startStation) => {
    //TODO: Implement your own method
    shuttles.forEach(shuttle => {
        if (shuttle.shuttleId === shuttleId) {
            shuttle.currentMix = mixId;
            shuttle.movements = movements[mixId][startStation.start][startStation.pos].instr;
            shuttle.intialMixSet = true;
            shuttle.currentMovePos = -1;
            // console.log('är vår movement uppdaterad?', shuttle);
        }
    });  
};