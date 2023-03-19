import paho.mqtt.client as mqtt_client
import threading
import json
from typing import final

class Interface:
    # Public interface functions
    def __init__(self, Address: str, Port: int, Name: str = "StudentProgram") -> None:
        self.Address = Address
        self.Port = Port
        self.CommandTopic = "aws_br/command"
        self.StatusTopic = "aws_br/status"

        # We create a mqtt client and bind internal callbacks to it
        self.__Client = mqtt_client.Client(Name)
        self.__Client.on_connect = self.__OnConnect
        self.__Client.on_message = self.__OnMessage

        # Allows for safe printing between threads
        self.__PrintLock = threading.Lock()
        #self.TransmitLock = threading.Lock()
    @final
    def Start(self) -> bool:
        self.__Client.connect(self.Address, self.Port)
        self.__Client.subscribe(self.StatusTopic)
        self.__Client.loop_start()
        return True
    @final
    def Stop(self) -> bool:
        self.__Client.loop_stop()
        self.__Client.disconnect()
        return True
    # Could probably be made to return a bool, instead of getting a callback with OnMoveDone
    @final 
    def Move(self, ShuttleID: int, Position: tuple[int]) -> None:
        pass
    @final
    def SetConfiguration(self, Configuration) -> None:
        pass
    @final 
    def SetMix(self, ShuttleID: int, Mix: str) -> None:
        Data = { "method": "SET_SHUTTLE_MIX", "id": ShuttleID, "mixId": Mix}
        self.__Client.publish(self.CommandTopic, json.dumps(Data))



    # External callback functions (does nothing if not assigned)
    # Overloading the functions must be done with the same function signature as the ones defined, but without the self argument
    def OnConnect(self) -> None:
        pass
    def OnOrderUpdate(self, ID: int, Data: dict) -> None:
        pass
    def OnHandover(self, ShuttleID: int) -> None:
        pass
    def OnMoveDone(self, ShuttleID: int) -> None:
        pass
    def OnProcessingDone(self, ShuttleID: int) -> None:
        pass
    def OnMixDone(self) -> None:
        pass
    def OnError(self, ErrorData) -> None:
        pass



    # Private functions
    # Aliasing function, that matches the function signature required by the mqtt client
    def __OnConnect(self, client, userdata, flags, rc):
        with self.__PrintLock:
            if rc == 0:
                print("Connection to server: SUCCESSFUL")
            else:
                assert False, "Connection to server: FAILED"
        self.OnConnect()

    # Delegating function, that decodes the incoming messages and calls the appropriate callback function
    def __OnMessage(self, client: mqtt_client, userdata, message):
        # We decode the message 
        Message = json.loads(message.payload.decode())
        Operation = Message['method']
        Data = Message['data']

        # We switch on the operation type
        match Operation:
            case "ORDER_UPDATED":
                ID = 0 # Constant for now, but could teoretically be any production order
                self.OnOrderUpdate(ID, Data)
                # Debugging
                with self.__PrintLock:
                    print("Order", ID)
                    print('| {:5} | {:3} | {:7} | {:9} |'.format("Mix", "Num", "Started", "Completed"))
                    for Mix in Data:
                        print('| {0[id]:5} | {0[quantity]:3} | {0[started]:7} | {0[completed]:9} |'.format(Mix))
            case "SHUTTLE_AT_START":
                ShuttleID = Data['shuttleId']
                self.OnHandover(ShuttleID)
                # Debugging
                with self.__PrintLock:
                    print("Shuttle", ShuttleID, "handed over")
            case "CONF":
                GridSize = [Data['rows'], Data['columns']]
                StationsGrid = self.__ConvertStationsToGrid(GridSize, Data['stations'])
                #ShuttlePositions = __
                # Debugging
                with self.__PrintLock:
                    print("")
            case "MOVE_DONE":
                ShuttleID = Data['shuttleId']
                self.OnMoveDone(ShuttleID)
                # Debugging
                with self.__PrintLock:
                    print("")
            case "PROCESSING_DONE":
                ShuttleID = Data['shuttleId']
                self.OnProcessingDone(ShuttleID)
                # Debugging
                with self.__PrintLock:
                    print("")
            case "MIX_ENDED":

                # Debugging
                with self.__PrintLock:
                    print("")
            case "REQUEST_NEW_MIX": pass
            case "FAILED": self.__OnError(Data)   
            case _: assert False, "Unrecognised command recieved"

    def __OnError(self, ErrorData) -> None:
        with self.__PrintLock:
            ErrorMsg = ""
            match ErrorData['errorId']:
                case 10000: ErrorMsg = "Shuttle ID not found"
                case 10001: ErrorMsg = "Shuttle currently in motion"
                case 10002: ErrorMsg = "Shuttle has not been assigned a mix"
                case 10003: ErrorMsg = "Shuttle attempted to move outside grid"
                case 10004: ErrorMsg = "Shuttle move command invalid"
                case 20000: ErrorMsg = "Station ID not found"
                case 20001: ErrorMsg = "Station still processing"
                case 20002: ErrorMsg = "Station lock attempt failed, station already locked"
                case 30001: ErrorMsg = "Mix assignment failed, mix is not completed"
                case _:     ErrorMsg = "Unrecognised error"

            print("Error:", ErrorMsg)
        self.OnError(ErrorData)

    def __ConvertStationsToGrid(self, GridSize: list, Stations: dict) -> list:
        pass