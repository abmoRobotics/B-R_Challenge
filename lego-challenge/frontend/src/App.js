import { useEffect, useRef, useState } from 'react';
import D3 from './components/D3';
import { useSetRecoilState, atom, useRecoilState } from 'recoil';
import Table from './components/Table';
import { startWebSocket } from './communication/WebSocket';
import { deleter, getter, setter } from './communication/Api';
import { Alert, Button, FormControl, Grid, ImageList, ImageListItem, InputLabel, MenuItem, Select, Snackbar } from '@mui/material';
//images
import brlogo from './images/logo.svg';

export const atConfiguration = atom({ key: 'configurationstate', default: { orders: [], colors: [], stations: [], rows: 0, columns: 0, shuttles: [] } });
export const atMoveShuttle = atom({ key: 'moveshuttlestate', default: { shuttleId: '', stationId: '', position: { x: 0, y: 0 } } });
export const atStation = atom({ key: 'stationstate', default: { stationId: '', color: '' } });
export const atError = atom({ key: 'errorstate', default: { error: '', code: 0 } });
export const atProcessTime = atom({ key: 'processState', default: { startTime: 0, endTime: 0 } });
export const atMixData = atom({ key: 'mixDataState', default: [] });


function App() {
    const [selectedShuttle, setSelectedShuttle] = useState(0);
    const [selectedStartPos, setSelectedStartPos] = useState(0);
    const [timeLapsed, setTimeLapsed] = useState(0);
    const [configuration, setConfiguration] = useRecoilState(atConfiguration);
    const [error, setError] = useRecoilState(atError);
    const [processTime, setProcessTime] = useRecoilState(atProcessTime);
    const setMoveShuttle = useSetRecoilState(atMoveShuttle);
    const setStation = useSetRecoilState(atStation);
    const [mixDone, setMixDone] = useRecoilState(atMixData);
    const [mixDoneTemp, setMixDoneTemp] = useState(0);
    const timer = useRef();

    useEffect(() => {
        setMixDoneTemp(mixDone);
    }, [mixDone])

    // creates a websocket 
    const webSocketOnMessage = async (e) => {
        // var dec = new TextDecoder();
        // console.log(e.data);
        // var data = dec.decode(e.data);
        let text = await e.data.text();
        // const message = JSON.parse(text);
        let message = JSON.parse(text);


        console.log(message)
        switch (message.method) {
            case 'CONF':
                stopTimer(processTime);
                setConfiguration(message.data)
                break;
            case 'MOVE':
            case 'MOVE_RETURN':
                setMoveShuttle(message.data);
                break;
            case 'PROCESSING':
            case 'PROCESSING_DONE':
                setStation(message.data);
                break;
            case 'MIX_STARTED':
            case 'MIX_ENDED':
                setProcessTime(message.data);
                break;
            case 'ORDER_UPDATED':
                setMixDone(message.data);
                break;
            default: console.log('METHOD communicated, did not exist:', message.method);
        }
    };

    useEffect(() => {
        // if (timer) clearInterval(timer);
        if (processTime.startTime === 0) return;
        if (processTime.endTime !== 0) {
            stopTimer(processTime);
        } else {
            startTimer(processTime);
        }
    }, [processTime]);

    const startTimer = (processTime) => {
        timer.current = setInterval(function () {
            var time = (Date.now() - processTime.startTime) / 1000;
            time = Math.floor(time);
            setTimeLapsed(time);
        }, 1000);
    }

    const stopTimer = (processTime) => {
        clearInterval(timer.current);
        timer.current = null;
        var time = (processTime.endTime - processTime.startTime) / 1000;
        setTimeLapsed(time);
    };

    const setConfigurationToBackend = async (e) => {
        console.log('sending config to backend');

        // TODO: Change configuration HERE!!!
        var boardConfig = {
            method: 'Config', type: 'POST', data: {
                rows: 6, columns: 7,
                stations: [
                    // row 1
                    { color: 'green', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'green', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'blue', time: 2, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'blue', time: 2, inuse: true },
                    //row 2
                    { color: 'green', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'green', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'blue', time: 2, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'blue', time: 2, inuse: true },

                    //row 3
                    { color: 'green', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'green', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'blue', time: 2, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'blue', time: 2, inuse: true },

                    //row 4
                    { color: 'blue', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'yellow', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'yellow', time: 2, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'green', time: 2, inuse: true },

                    //row 5
                    { color: 'yellow', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'yellow', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'yellow', time: 2, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'yellow', time: 2, inuse: true },

                    //row 6
                    { color: 'blue', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'yellow', time: 1, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'yellow', time: 2, inuse: true },
                    { color: 'grey', time: 2 },
                    { color: 'green', time: 2, inuse: true },

                ],
                shuttles: [
                    {
                        id: '0',
                    }, {
                        id: '1'
                    }, {
                        id: '2'
                    }, {
                        id: '3'
                    }, {
                        id: '4'
                    }, {
                        id: '5'
                    }, {
                        id: '6'
                    }, {
                        id: '7'
                    }, {
                        id: '8'
                    }, {
                        id: '9'
                    }, {
                        id: '10'
                    }, {
                        id: '11'
                    }, {
                        id: '12'
                    }, {
                        id: '13'
                    }, {
                        id: '14'
                    }
                ],
                orders: [{
                    id: 'Mix A',
                    quantity: 4,
                    recipe: [{
                        color: "green",
                        quantity: 2
                    }, {
                        color: "yellow",
                        quantity: 1
                    }]
                }, {
                    id: 'Mix B',
                    quantity: 2,
                    recipe: [{
                        color: "blue",
                        quantity: 1
                        // },{
                        //     color: "yellow",
                        //     quantity: 1
                    }]
                }, {
                    id: 'Mix C',
                    quantity: 3,
                    recipe: [{
                        color: "green",
                        quantity: 1
                    }, {
                        color: "blue",
                        quantity: 1
                    }]
                }, {
                    id: 'Mix D',
                    quantity: 2,
                    recipe: [{
                        color: "yellow",
                        quantity: 1
                    }, {
                        color: "blue",
                        quantity: 1
                    }]
                }]
            }
        }
        // let message = JSON.stringify(boardConfig); 
        // sendWebSocketMessage(message);
        let data = await setter('/config', boardConfig);
        if (data.error) {
            setError(data.data);
        }
    };

    const getConfigurationFromBackend = async () => {
        let data = await getter('/config');
        if (data.error) {
            setError(data.data);
        } else {
            console.log(data.board);
        }

    }

    const moveTo = async (dir) => {
        let data = await setter('/shuttle/move/' + selectedShuttle + '/' + dir, {});
        if (data.error) {
            setError(data.data);
        }
    }

    const moveToStart = async () => {
        let data = await setter('/move/shuttle/' + selectedShuttle + '/to/start/pos/' + selectedStartPos, {});
        if (data.error) {
            setError(data.data);
        }
    }

    const moveStartlane = async () => {
        getter('/shuttle/0/set/mix/Mix A');
        getter('/shuttle/1/set/mix/Mix A');
        getter('/shuttle/2/set/mix/Mix A');
        getter('/shuttle/3/set/mix/Mix A');
        getter('/shuttle/4/set/mix/Mix A');
        getter('/shuttle/5/set/mix/Mix A');
        getter('/shuttle/6/set/mix/Mix A');
        setter('/shuttle/move/0/f', {});
        setter('/shuttle/move/1/f', {});
        setter('/shuttle/move/2/f', {});
        setter('/shuttle/move/3/f', {});
        setter('/shuttle/move/4/f', {});
        setter('/shuttle/move/5/f', {});
        setter('/shuttle/move/6/f', {});
        setSelectedShuttle('7')
    }

    //react hooks
    useEffect(() => {
        startWebSocket(webSocketOnMessage);
    }, [])

    const resetBoard = () => {
        deleter('/config');
    }

    const setMixToShuttle = async (mix) => {
        await getter('/shuttle/' + selectedShuttle + '/set/mix/' + mix);
    }

    const selectShuttleToMove = (e) => {
        setSelectedShuttle(parseInt(e.target.value));
    }

    const selectStartPosToMoveShuttleTo = (e) => {
        setSelectedStartPos(parseInt(e.target.value));
    }

    return (
        <>
            <Grid container spacing={2}>
                <Grid item xs={1} />
                <Grid item xs={2} >
                    <ImageList sx={{ width: 200, height: 75, display: 'block' }} cols={1} rowHeight={'auto'} >
                        <ImageListItem>
                            <img
                                src={brlogo}
                                alt="B&R logo type in svg format"
                                loading="lazy"
                            />
                        </ImageListItem>
                    </ImageList>
                </Grid>
                <Grid item xs={4} ><h1>B&R-AWS-LEGO Student challenge</h1></Grid>
                <Grid item xs={2} >
                    <h3>
                        {
                            (timeLapsed > 0) ? 'Time lapsed: ' + timeLapsed + ' s' : null
                        }
                    </h3>
                </Grid>
            </Grid>
            <Grid container spacing={2}>
                <Grid item xs={12} md={7} lg ={6}>
                    <D3 />
                </Grid>
                <Grid item xs={12} md={5} lg={6} >
                    <Table />
                </Grid>
            </Grid>
            <Grid container spacing={2}>
                <Grid item xs={12} >

                    <Button onClick={() => setConfigurationToBackend()}>Set configuration</Button>
                    <Button onClick={() => getConfigurationFromBackend()}>Get configuration</Button>
                    <Button color="warning" onClick={() => moveTo('l')}>Move left </Button>
                    <Button color="warning" onClick={() => moveTo('f')}>Move forward</Button>
                    <FormControl>
                        <InputLabel id="demo-simple-select-label">Shuttle</InputLabel>
                        <Select
                            labelId="demo-simple-select-label"
                            id="demo-simple-select"
                            value={configuration?.shuttles[selectedShuttle]?.id || 0}
                            label="Shuttle"
                            onChange={selectShuttleToMove}
                        >
                            {
                                configuration.shuttles.map((shuttle, idx) => {
                                    return <MenuItem key={idx} value={shuttle.id}>Shuttle {shuttle.id}</MenuItem>
                                })
                            }
                        </Select>
                    </FormControl>
                    <Button color="warning" onClick={() => moveTo('b')}>Move backward</Button>
                    <Button color="warning" onClick={() => moveTo('r')}>Move right</Button>
                    <Button color="error" onClick={() => resetBoard()}>Restore board</Button>
                </Grid>
                <Grid item xs={12} >
                    <Button color="info" onClick={() => moveStartlane()}>Move start lane</Button>
                    <Button color="info" onClick={() => setMixToShuttle('Mix A')}>Set Mix A</Button>
                    <Button color="info" onClick={() => setMixToShuttle('Mix B')}>Set Mix B</Button>
                    <Button color="info" onClick={() => setMixToShuttle('Mix C')}>Set Mix C</Button>
                    <Button color="info" onClick={() => moveToStart()}>Move shuttle to start pos</Button>
                    <FormControl>
                        <InputLabel id="demo-simple-select-label">Starting Position</InputLabel>
                        <Select
                            labelId="demo-simple-select-label"
                            id="demo-simple-select"
                            label="Starting Position"
                            onChange={selectStartPosToMoveShuttleTo}
                        >
                            <MenuItem value={'Start_00'}>Start_00</MenuItem>
                            <MenuItem value={'Start_01'}>Start_01</MenuItem>
                            <MenuItem value={'Start_02'}>Start_02</MenuItem>
                            <MenuItem value={'Start_03'}>Start_03</MenuItem>
                            <MenuItem value={'Start_04'}>Start_04</MenuItem>
                            <MenuItem value={'Start_05'}>Start_05</MenuItem>
                            <MenuItem value={'Start_06'}>Start_06</MenuItem>
                        </Select>
                    </FormControl>
                </Grid>
            </Grid>
            {
                (error.status > 200) ?
                    <Snackbar autoHideDuration={2000} >
                        <Alert severity="error" sx={{ width: '100%' }}>
                            Code {error.status}: {error.message}
                        </Alert>
                    </Snackbar> : null
            }
        </>
    );
}

export default App;
