from paho.mqtt import client as mqtt_client
import json
from commands_enum import Commands
from threading import Timer
from threading import Thread
from time import sleep
from model import Model, get_movement_instructions_from_path, flatten
from estimator.problem.find_paths import global_graph, reduced_combinations, VARIANT_MIXES, COLOR_MAP, get_key_from_value
import time
# static data for connecting
broker = 'localhost' #192.168.99.110
port = 1883
topic_cmd = "aws_br/command"
topic_status = "aws_br/status"
client_id = f'python-mqtt-student-machine'
#Global variables
sleeper = 0.1 #sec

# Save the current paths of the shuttles
current_paths = {str(shuttleId): [] for shuttleId in range(15)}

# Opening JSON files
#f = open('example_program/py/data/board.feed.data_6x7_1.json')
f = open('example_program/py/data/board.feed.data.json')
board = json.load(f)
f.close()

# Start our model
model = Model(global_graph, reduced_combinations, VARIANT_MIXES)

def threadedNextMove(client: mqtt_client, id, dir):
    # Timer(2, getDeferredNextMove, (client, id, dir))
    sleep(sleeper)
    # print('moving next shuttle')
    data = {"method": "MOVE_SHUTTLE_TO", "id": id, "direction": dir}
    dump = json.dumps(data)
    client.publish(topic_cmd, dump)

def threadedMoveShuttleToStart(client: mqtt_client, id, startLane):
    sleep(sleeper)
    # print('moving next shuttle')
    data = {"method": "MOVE_SHUTTLE_TO_START", "id": id, "stationId": startLane}
    dump = json.dumps(data)
    client.publish(topic_cmd, dump)

def init_cmd(client: mqtt_client, topic):
    initConfig = {"method": "SET_CONF", "type": "POST", "data": board }
    dump = json.dumps(initConfig)
    client.publish(topic, dump)

def send_data(client: mqtt_client, telegram):
    # print(telegram)
    time.sleep(sleeper)
    dump = json.dumps(telegram)
    client.publish(topic_cmd, dump)
    # thread = Thread(target=deferred_send_data, args=(client, telegram))
    # thread.start()

def deferred_send_data (client: mqtt_client, telegram):
    sleep(sleeper)
    # print(telegram)
    dump = json.dumps(telegram)
    client.publish(topic_cmd, dump)

def connect ():

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            init_cmd(client, topic_cmd)
        else:
            assert False, f'Failed to connect, return code {rc}'
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def switch_status (client: mqtt_client, telegram):
    if telegram['method'] == "ORDER_UPDATED":
            # When the order data is updated we can keep track on what needs to be done
            model.set_finished_orders(telegram['data'])
    
    elif telegram['method'] == "CONF":
            # //First get initial mixes and set all shuttles to these
            mixes = model.get_initial_mixes(board['columns'])
            shortestPaths = []
            for col, mix in enumerate(mixes):
                mix_telegram = { "method": "SET_SHUTTLE_MIX", "id": mix['shuttleId'], "mixId": mix['mixId'] }
                send_data(client, mix_telegram)

                # Find the shortest path going through these stations (and no others)
                pathSegments = model.find_optimal_path_from_stations(mix['stationsToVisit'], start_node=f"{col}_start")
                shortestPaths.append(flatten(pathSegments))
                current_paths[mix['shuttleId']] = pathSegments
                
                # Update the global graph in the model for the first path segment
                model.graph.update_weights(pathSegments[0], model.combinations)

                # Set initial positions
                model.set_start_position(mix['shuttleId'],x=col)
            
            sleep(sleeper)
            
            moves = model.get_initial_moves(board['columns'], shortestPaths)
            for firstMove in moves:
                move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": firstMove['shuttleId'], "direction": firstMove['move'] }
                send_data(client, move_telegram)

    elif telegram['method'] == "MOVE_DONE":
        # Update current position of shuttle
        model.update_position(telegram['data']['shuttleId'])
        
        if telegram['data']['inuse'] == False:
            dir = model.get_next_move(telegram['data']['shuttleId'])
            if (dir is not None):
                move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": telegram['data']['shuttleId'], "direction": dir }
                send_data(client, move_telegram)
                #time.sleep(0.1)

    elif telegram['method'] == "PROCESSING_DONE":
        # Get the previous and current segments from the path and remove it from the list

        # TODO: This is not the best way to do this, but it works for now
        if current_paths[telegram['data']['shuttleId']] == []:
            # If the list is empty, the shuttle is done
           
            # Move the shuttle to the start lane
            print(f'Shuttle {telegram["data"]["shuttleId"]} is done! only going forwards')
            move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": telegram['data']['shuttleId'], "direction": 'f' }
            send_data(client, move_telegram)
            
            return
        else:
            previous_pathSegment = current_paths[telegram['data']['shuttleId']].pop(0)
        try:
            next_pathSegment = current_paths[telegram['data']['shuttleId']][0]
                
            # Reset the weights from the previous path segment and update the weights for the next path segment
            model.graph.update_weights(previous_pathSegment, model.combinations, reset_weights=True)
            model.graph.update_weights(next_pathSegment, model.combinations)
        except IndexError:
            pass
        
        color = get_key_from_value(COLOR_MAP, telegram['data']['color'])
        model.processingDone(telegram['data']['shuttleId'], color)
        dir = model.get_next_move(telegram['data']['shuttleId'])
        if (dir is not None):
            move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": telegram['data']['shuttleId'], "direction": dir }
            send_data(client, move_telegram)

    elif telegram['method'] == "FAILED":
        if (telegram['error'] is not None):
            if (telegram['error']['errorId'] == 20001 or telegram['error']['errorId'] == 20002):
                # If the target station is locked (20001) or still processing (20002) keep sending the same telegram
                # over and over again untill the desired station is free
                #dir = model.get_current_move(telegram['error']['shuttleId'])
                
                #if model.check_headon_collision(telegram['error']['shuttleId']):
                # Replan if station is occupied or processing
                model.replan(telegram['error']['shuttleId'])
                dir = model.get_next_move(telegram['error']['shuttleId'])

                if (dir is not None):
                    move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": telegram['error']['shuttleId'], "direction": dir }
                    send_data(client, move_telegram)

            if telegram['error']['errorId'] == 20003:
                # If the start station is locked (20003) send the same move command again
                    print('starting timer to move next in 2 sec')
                    thread = Thread(target=threadedMoveShuttleToStart, args=(client, telegram['error']['shuttleId'], telegram['error']['startLane']))
                    thread.start()
            
            if telegram['error']['errorId'] == 10007:
                # If the shuttle hasnt reached the start station yet (10007) send the same move command again
                    print('starting timer to move next in 2 sec')
                    thread = Thread(target=threadedMoveShuttleToStart, args=(client, telegram['error']['shuttleId'], telegram['error']['startLane']))
                    thread.start()
            
            if telegram['error']['errorId'] == 10006:
                # If the shuttle is trying to move outside of the scope of the board, do something else
                    # dir = model.get_current_move(telegram['error']['shuttleId'])
                    # if dir == 'l': 
                    #     dir = 'r'
                    # if dir == 'r': 
                    #     dir = 'l'
                    # # print('starting timer to move next in 2 sec')
                    # TODO: handle an error where we are trying to move outsie of the scope 
                    # thread = Thread(target=threadedNextMove, args=(client, telegram['error']['startLane'], dir))
                    # thread.start()
                pass
        else:
            print('Strange things arrived', telegram)

    elif telegram['method'] == "MIX_ENDED":
            # When the mix has ended, print data and exit the process. Optimize the code
            print('total time', (telegram['data']['endTime'] - telegram['data']['startTime']) / 1000, 's', 'avg utilisation', telegram['data']['averageUtilization'], 'stationwise utilisation', telegram['data']['utilizationPerStation'])
            print('Please optimise avg and stationwise utilisation first and then total time, your time score is:',telegram['data']['timeScore'])
            quit(0)
    
    elif telegram['method'] == "SHUTTLE_AT_START":
        move_telegram = None
        startStation = None
        mix = None
        
        model.reset_move(telegram['data']['shuttleId'])
        # A potentially unncessary check, but make sure the shuttle is reset on local side aswell before proceeding 
        if (model.is_move_reset(telegram['data']['shuttleId'])):
            # Here we start the returning of shuttles
            # First off, check if we are finished: i.e. all mixes have shuttles asigned to them
            weAreFinished = areWeFinished()
            print('are we finished?', weAreFinished)

            if (not weAreFinished):
                mix = model.get_next_mix(telegram['data']['shuttleId'])
                # build telegram and send
                mix_telegram = { "method": "SET_SHUTTLE_MIX", "id": telegram['data']['shuttleId'], "mixId": mix }
                send_data(client, mix_telegram)

                # if a mix is returned - i.e. something is left to gather, we build the name of the start station and set next movement.
                if (mix is not None):
                    # Get the best combination of stations to visit based on the mix
                    stationsToVisit = model.get_stations_to_visit(mix)
                    
                    # Find the shortest path going through these stations (and no others)
                    pathSegments = model.find_optimal_path_from_stations(stationsToVisit)
                    shortestPath = flatten(pathSegments)
                    current_paths[telegram['data']['shuttleId']] = pathSegments
                    
                    # Convert the path to movements
                    movements, startPos = get_movement_instructions_from_path(shortestPath)
                    startStation = ('Start_0' + str(startPos))
                    model.set_start_position(telegram['data']['shuttleId'], x=startPos)
                    # Set the next movement for the given shuttle
                    model.set_next_movement(telegram['data']['shuttleId'], mix, movements)
                    
                    # Update the global graph in the model for the first path segment
                    model.graph.update_weights(pathSegments[0], model.combinations)

            if weAreFinished:
                # If we are finished, we only want to move the shuttle to a start station and do nothing else
                once = model.getOnce()
                startStation = 'Start_0' + str(once)
                # Make sure we only update the once variable the number of columns we have
                if (once < board['columns']): 
                    once += 1
                    model.setOnce(once)
                
            move_telegram = { "method": "MOVE_SHUTTLE_TO_START", "id": telegram['data']['shuttleId'], "stationId": startStation }
            # If we have a move telegram we send it
            
            # await setTimeoutP(1000)
            send_data(client, move_telegram)

    elif telegram['method'] == "REQUEST_NEW_MIX":
        # Naming convesion here is a bit off, we could see it as a start for the shuttle to move out on the board
        firstMoveDir = model.get_next_move(telegram['data']['shuttleId'])
        next_move_telegram = { "method": "MOVE_SHUTTLE_TO", "id": telegram['data']['shuttleId'], "direction": firstMoveDir }
        send_data(client, next_move_telegram)


def areWeFinished():
    # iterate over all orders and compare quantity to started to see if we need to send more 
    # shuttles or not
    totalQuantity = 0
    totalStarted = 0
    finished_orders = model.get_finished_orders()
    print(finished_orders)
    for order in finished_orders:
        totalQuantity += order['quantity']
        totalStarted += order['started']
    print('Evaluating quantities', totalQuantity, 'and finished', totalStarted)
    
    return totalQuantity == totalStarted

def subscribe(client: mqtt_client, topic):
    def on_message(cli, userdata, msg):
        rcvd_data = msg.payload.decode()
        # print(f"Received `{rcvd_data}` from `{msg.topic}` topic")
        data = json.loads(rcvd_data)
        # switch_status(client, data)
        print('new thread started with status', data['method'])
        thread = Thread(target=switch_status, args=(client, data))
        thread.start()

    client.subscribe(topic)
    client.on_message = on_message


# Defining main function
def main():
    try:
        print('Connecting')
        mqtt_client = connect()
        print('Subscribing')
        subscribe(mqtt_client, topic_status)
        # init_cmd(mqtt_client, topic_cmd)
        print('Starting loop')
        mqtt_client.loop_forever()
    except AssertionError as msg:
        print(msg)

# Using the special variable
# __name__
if __name__=="__main__":
    main()