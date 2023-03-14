import config from './config.json';

const ws = {};

export const startWebSocket = (webSocketOnMessage) => {
    if (!ws.current) {
        ws.current = new WebSocket(config.websocket);
        ws.current.onopen = webSocketOnOpen;
        ws.current.onclose = webSocketOnClose;
        ws.current.onmessage  = webSocketOnMessage;
    }

};

export const webSocketOnOpen = () => {
    console.log("ws opened");
};

export const webSocketOnClose = () => {
    console.log("ws closed");
};

export const sendWebSocketMessage = (mes) => {
    var enc = new TextEncoder(); // always utf-8
    ws.current.send(enc.encode(mes));
};


export const closeWebSocket = () => {
    ws.current.close();
};