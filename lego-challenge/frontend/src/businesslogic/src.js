import Sim6D from "./Sim6D"

const margin = { top: 20, bottom: 20, left: 20, right: 20 };

const layout = {margin: margin, height: 800 - margin.top - margin.bottom, width: 800 - margin.left - margin.right};
const Data = {
    layout: {rows: 5, columns: 4},
    stations: [{
        id: 'psR0C0', time: 1, state: 'idle'
    },{
        id: 'psR0C1', time: 1, state: 'idle'
    },{
        id: 'psR0C2', time: 1, state: 'idle'
    },{
        id: 'psR0C3', time: 1, state: 'idle'
    },{
        id: 'psR1C0', time: 1, state: 'idle'
    },{
        id: 'psR1C1', color: 'green', time: 1, state: 'idle'
    },{
        id: 'psR1C2', time: 1, state: 'idle'
    },{
        id: 'psR1C3', time: 1, state: 'idle'
    },{
        id: 'psR2C0', time: 1, state: 'idle'
    },{
        id: 'psR2C1', time: 1, state: 'idle'
    },{
        id: 'psR2C2', color: 'red', time: 1, state: 'idle'
    },{
        id: 'psR2C3', time: 1, state: 'idle'
    },{
        id: 'psR3C0', time: 1, state: 'idle'
    },{
        id: 'psR3C1', time: 1, state: 'idle'
    },{
        id: 'psR3C2', color: 'blue', time: 1, state: 'idle'
    },{
        id: 'psR3C3', time: 1, state: 'idle'
    },{
        id: 'psR4C0', time: 1, state: 'idle'
    },{
        id: 'psR4C1', time: 1, state: 'idle'
    },{
        id: 'psR4C2', time: 1, state: 'idle'
    },{
        id: 'psR4C3', time: 1, state: 'idle'
    }]
    ,
    order:  [{
        id: 'Mix A',
        quantity: 5,
        recipe: [{
            color: "Blue",
            quantity: 2
        },{
            color: "Yellow",
            quantity: 3
        }]
    },{
        id: 'Mix B',
        quantity: 6,
        recipe: [{
            color: "Blue",
            quantity: 1
        },{
            color: "Yellow",
            quantity: 1
        }]
    }, {
        id: 'Mix C',
        quantity: 3,
        recipe: [{
            color: "Yellow",
            quantity: 3
        },{
            color: "Green",
            quantity: 4
        }]
    }],
    shuttles: [{
        id: 0
    },
    {
        id: 1
    },{
        id: 2
    }]
}

function main(){

    

    let SimObj = new Sim6D(layout);
    SimObj.initialize6D(Data);

    // For demonstration, moving the shuttles randomly
    moveRandomShuttles(SimObj);
}


// Only for demonstrating the shuttles moving
function moveRandomShuttles(simObj){
    const shuttleDuration = 200;
    const durationBetweenMovements = 200;

    function moveRandomShuttle(){
        const randomIdx = Math.floor(Math.random() * simObj.shuttles.length);
        const randomShuttle = simObj.shuttles[randomIdx];
        const shuttlePos = {x: randomShuttle.pos.x, y: randomShuttle.pos.y};
        

        // Move horizontally or vertically
        const randomNum = Math.random();
        let newShuttlePos = shuttlePos;
        if (randomNum < 0.25){              // Up
            newShuttlePos.y++;  
        }else if (randomNum < 0.5){         // Down
            newShuttlePos.y--;
        }else if (randomNum < 0.75){        // Left
            newShuttlePos.x--;
        }else{                              // Right
            newShuttlePos.x++;
        }

        const movementOK = newShuttlePos.x >= 0 && newShuttlePos.x < simObj.numColumns && newShuttlePos.y >= 0 && newShuttlePos.y < simObj.numRows && simObj.shuttles.findIndex(x => x.pos.x === newShuttlePos.x && x.pos.y === newShuttlePos.y) === -1;

        if (movementOK){
            simObj.moveShuttle(randomShuttle.id, newShuttlePos, shuttleDuration);
            setTimeout(() => {
                moveRandomShuttle();
            }, durationBetweenMovements)
        }else{
            moveRandomShuttle();
        }
    }


    moveRandomShuttle()
}


//main();