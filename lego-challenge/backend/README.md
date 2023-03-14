# Getting Started with the B&R simulation project

This simulation was built by [B&R](https://www.br-automation.com/). To run this script you will need one of the latest [NodeJS](https://nodejs.org/en/download/) versions installed. If you already have a version of NodeJs installed I highly recommend using nvm (Node Version Manager) to control the different versions. You find them here
[Linux/Mac](https://github.com/nvm-sh/nvm) or for [Windows](https://github.com/coreybutler/nvm-windows)

## Available Scripts

In the project directory, you can run:

### `npm run dev`

Runs the app in the development mode.\
This will start the simulation on [http://localhost:3001](http://localhost:3001).

## Send commands
To integrate and command the shuttles you have a few different was to do this.
First one is to use an MQTT broker with commands, and another way is to use a classic REST API.

### MQTT broker
If you elect to use the MQTT broker to send commands, you will need to install (locally) a broker on your end (or use the AWS pre configured one in the cloud).\
you will then need to implement a client, or get one either via [npm](https://www.npmjs.com/package/mqtt) or [pip](https://pypi.org/project/mqtt-client/).

Set the broker path in enum/mqttenum.json BROKER_PATH. Example: mqtt://localhost 

### MQTT TOPIC STRUCTURE
aws_br  -> command  (Sub)
        -> status   (Pub)
        -> board    (Pub)

The user publishes commands onto the command topic.
System responds with statuses on the status topic.
Board topic contains a complete image of the board states.

#### Commands you can send
There are 4 different commands you can send. The first one will set the configuration, the second one will assign a mix to a shuttle, the third; a command to 
move a shuttle one step forward (backwards, right or left) and finally a command to move the shuttle to a given starting position. 
Examples follow with windows program [mosquitto](https://mosquitto.org/):

##### SET_CONF: 
mosquitto_pub.exe -t "aws_br/command" -m "{\"method\":\"SET_CONF\",\"type\":\"POST\",\"data\":{\"rows\":3,\"columns\":3,\"stations\":[{\"color\":\"green\",\"time\":1,\"inuse\":true},{\"color\":\"blue\",\"time\":2,\"inuse\":true},{\"color\":\"grey\",\"time\":2},{\"color\":\"green\",\"time\":1,\"inuse\":true},{\"color\":\"grey\",\"time\":2},{\"color\":\"blue\",\"time\":2,\"inuse\":true},{\"color\":\"yellow\",\"time\":3,\"inuse\":true},{\"color\":\"grey\",\"time\":2},{\"color\":\"green\",\"time\":1,\"inuse\":true}],\"shuttles\":[{\"id\":\"0\"},{\"id\":\"1\"},{\"id\":\"2\"}],\"orders\":[{\"id\":\"Mix A\",\"quantity\":1,\"recipe\":[{\"color\":\"green\",\"quantity\":2},{\"color\":\"yellow\",\"quantity\":1}]},{\"id\":\"Mix B\",\"quantity\":1,\"recipe\":[{\"color\":\"blue\",\"quantity\":1}]},{\"id\":\"Mix C\",\"quantity\":1,\"recipe\":[{\"color\":\"green\",\"quantity\":1},{\"color\":\"blue\",\"quantity\":1}]}]}}"

##### SET_SHUTTLE_MIX: 
mosquitto_pub.exe -t "aws_br/command" -m "{\"method\": \"SET_SHUTTLE_MIX\", \"id\": 0, \"mixId\": \"Mix A\"}"

##### MOVE_SHUTTLE_TO: 
mosquitto_pub.exe -t "aws_br/command" -m "{\"method\": \"MOVE_SHUTTLE_TO\", \"id\": \"2\", \"direction\": \"f\"}"

##### MOVE_SHUTTLE_TO_START
mosquitto_pub.exe -t "aws_br/command" -m "{\"method\": \"MOVE_SHUTTLE_TO_START\", \"id\": \"2\", \"stationId\": \"Start_05\" }

#### Staus returned to you
When You send a command down, a series of statuses will be returned. These are mostly for the front end to update the view of the simulation, but could also be good for you to know the state the board.

##### CONF

##### ORDER_UPDATED
This id corresponds to which orders exists (as specified in the SET_CONF), the quantity which should be filled and how many have been completed so far

eg: {"method":"ORDER_UPDATED","data":[{"id":"Mix A","quantity":1,"completed":0},{"id":"Mix B","quantity":1,"completed":0},{"id":"Mix C","quantity":1,"completed":0}]}
eg: {"method":"ORDER_UPDATED","data":[{"id":"Mix A","quantity":1,"completed":1},{"id":"Mix B","quantity":1,"completed":1},{"id":"Mix C","quantity":1,"completed":1}]}

##### MIX_STARTED
This will be triggered at the first move. This will store the start time and will be triggered again when all orders are filled and will then have the end time so you will be able to measure the algos total time. This is the value you should optimize (See MIX_ENDED). 

eg: {"method":"MIX_STARTED","data":{"startTime":1670252794268,"endTime":0}}

##### MOVE
Triggered by a MOVE_SHUTTLE_TO command. Right before the shuttle moves, the MOVE is sent.

eg. {"method":"MOVE","data":{"shuttleId":"0","newStationId":"PS10","position":{"x":0,"y":2}}}

##### MOVE_DONE
When the move has been finished, the MOVE_DONE is sent.

eg. {"method":"MOVE_DONE","data":{"shuttleId":"0","stationId":"PS10"}}

##### PROCESSING
Should the shuttle move under a processing station, the processing station will automatically fill the shuttle with whatever it contains
This method will be sent out.

eg. {"method":"PROCESSING","data":{"stationId":"PS10","color":"red"}}

##### PROCESSING_DONE
After the processing time, specified in the SET_CONF, the process is done this command is sent.

eg. {"method":"PROCESSING_DONE","data":{"stationId":"PS10","color":"green"}}

##### MIX_ENDED
Same as MIX_STARTED but with endTime specified, it will also give you a time score which is the value you need to optimize.
It will also produce the average utilization over all stations (Utilization or OEEE is a measurement of how much time the machine 
is actively producing over the total time) and the utilization for each individual station. Therefore you can see which stations
to optimize or remove. 

The time score is calculated as:
time score = SUM(station_production_cost) + SUM(alpha / station_utilization) + (1 - alpha)*total_time

alpha is a weight between 1 and 0.
station production cost is parameter which will punish you if you add too many stations to the board
sum of station utilization is the inverse of the time the machine is running, the more it is producing the lower the value it will have
finally you have the total time which the lower it get's the better the performance.
total time is not as heavily weighted as the station utilization.

the value time score should be _minimized_! Good luck


telegram will look like:

eg. {"method":"MIX_ENDED","data":{"startTime":1670403117563,"endTime":1670403132906, averageUtilization: 0.0753850607412731, utilizationPerStation: {
  PS02: 0.12044440451591651,
  PS26: 0.12029467253616027,
  PS42: 0.030305752702662236,
  PS52: 0.06055161261342198,
  PS56: 0.06049171982151948
},"timeScore": 14682.755208337863}}


##### SHUTTLE_AT_START
When a shuttle has reached the handover position it will send this status. This means you can call the shuttle using the  MOVE_SHUTTLE_TO_START command and specify which
starting position the shuttle should go to. Once the shuttle is there the status REQUEST_NEW_MIX will be sent out.

##### REQUEST_NEW_MIX
When a shuttle is at a starting position it will send the request for a new mix (setting a mix is required before you can move the shuttle out on the board), which you can use
to first set the mix and then immediately call the move command afterwards. There is no response from the shuttle if the mix has been set, so you need to take the initiative
and move the shuttle afterwards.

#### Failed commands
Everyone once in a while you will run into an issue where you issue a command and it is rejected by the simulation. For example trying to move a shuttle out of a process
while the process is running. Then an error command is returned. It contains data about which method failed, the id of the shuttle, and an error id and a message.

eg. {"method":"FAILED","failedMethod":"MOVE_SHUTTLE_TO","id":"4","error":10000,"message":"No shuttle found"}

#### Error Ids:
Possible error commands the program can send

##### NO_SHUTTLE_FOUND - 10000
You are trying to access a shuttle with an id that doesnt exist

##### SHUTTLE_ALREADY_MOVING - 10001
The shuttle you are trying to move is already moving

##### NO_MIX_ASSIGNED_TO_SHUTTLE - 10002
The shuttle you are trying to move doesn't have a mix assigned, it cannot be moved. 

##### SHUTTLE_OUT_OF_BOUNDS - 10003
You are trying to move a shuttle out of bounds of the grid. Action not allowed

##### INVALID_SHUTTLE_MOVE_COMMAND - 10004
The command you've used to move the shuttle didnt exist, please make sure it's either
f, b, l, r or forth, back, left or right.

##### NO_STATION_FOUND - 20000
The station you are trying to access does not exist.

##### STATION_STILL_PROCESSING - 20001
The station is still processing the shuttle, you cannot move it.

##### STATION_LOCKED - 20002
The station is locked by another or your shuttle, you cannot lock it again.

##### MIX_IS_NOT_FINISHED - 30001
The mix assigned to a shuttle isn't finished, you cannot change it while it's being processed.

### REST API
It is also possbile to communicate with a classical REST API. This is however not recommended, as the response will not be triggered until\
the whole process with the move and everything is done, so the response time back to the server/your application will be slower.
For more information on which endpoints to call, see section on Swagger UI.

#### Swagger UI

The simulation comes with a swagger ui to show all the possible endpoints that you can call.\
Start the simulation and go to [http://localhost:3001/api-docs/#/](http://localhost:3001/api-docs/#/).
