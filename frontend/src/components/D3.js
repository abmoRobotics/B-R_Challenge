import { useRecoilValue } from "recoil";
import Sim6D from "../businesslogic/Sim6D";
import { atConfiguration, atMoveShuttle, atStation } from '../App';
import { useEffect, useMemo } from "react";

function D3 (props) {

    const configuration = useRecoilValue(atConfiguration);
    const shuttle = useRecoilValue(atMoveShuttle);
    const station = useRecoilValue(atStation);

    const margin = { top: 20, bottom: 20, left: 20, right: 20 };

    const layout = {margin: margin, height: 800 - margin.top - margin.bottom, width: 800 - margin.left - margin.right};
    const data = {
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

    const simObj = useMemo(() => { return new Sim6D(layout)}, [Sim6D]);
    
    useEffect(() => {
        simObj.initialize6D(configuration);
    }, [configuration, simObj])

    useEffect(() => {
        if (shuttle.shuttleId !== '') simObj.moveShuttle(shuttle.shuttleId, shuttle.position, 1000);
    }, [shuttle, simObj]);

    useEffect(() => {
        if (station.stationId !== '') simObj.setProcessingStationColor(station.stationId, station.color);
    })

    return (
        <>
            <div id="d3-main" />
        </>
    )
}

export default D3;