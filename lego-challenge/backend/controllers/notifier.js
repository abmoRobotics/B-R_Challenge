const url = require("url");
const { Server } = require("ws");

/**
 * This class will create a websocket to the front end so that data can be pushed
 * to the frontend and the HMI updated.
 */
class NotifierService {
  constructor() {
    this.connections = new Map();
  }

  connect(server) {
    this.server = new Server({ noServer: true });
    this.interval = setInterval(this.checkAll.bind(this), 10000);
    this.server.on("close", this.close.bind(this));
    this.server.on("connection", this.add.bind(this));
    server.on("upgrade", (request, socket, head) => {
      const id = url.parse(request.url, true).query.storeId;
      if (id) {
        this.server.handleUpgrade(request, socket, head, (ws) =>
          this.server.emit("connection", id, ws)
        );
      } else {
        socket.destroy();
      }
    });
    console.log("ws server");
  }

  add(id, socket) {
    console.log("ws add");
    socket.isAlive = true;
    socket.on("pong", () => (socket.isAlive = true));
    socket.on("close", this.remove.bind(this, id));
    this.connections.set(id, socket);
  }

  send(id, message) {
    // console.log("ws sending message");
    const connection = this.connections.get(id);
    message.time = Date.now();

    var enc = new TextEncoder('utf-8');
    var data = enc.encode(JSON.stringify(message));
    if (connection) {
      try {
        connection.send(data);
      } catch (err) {
        console.log('Trying to send data failed for',id,', reason:', err.message)
      }
    }
  }

  broadcast(message) {
    console.log("ws broadcast");
    this.connections.forEach((connection) => {
        var enc = new TextEncoder('utf-8');
        var data = enc.encode(JSON.stringify(message));
        // console.log(data);
        if (connection) {
          try {
            connection.send(data);
          } catch (err) {
            console.log('Trying to send data failed, reason:', err.message)
          }
        }
    }
    );
  }

  isAlive(id) {
    return !!this.connections.get(id);
  }

  checkAll() {
    this.connections.forEach((connection) => {
      if (!connection.isAlive) {
        return connection.terminate();
      }

      connection.isAlive = false;
      connection.ping("");
    });
  }

  remove(id) {
    this.connections.delete(id);
  }

  close() {
    clearInterval(this.interval);
  }
}

module.exports = NotifierService;