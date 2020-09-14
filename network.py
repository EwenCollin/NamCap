import math
import json


def send_data(data, socket):
    data = "start_of_data" + data + "end_of_data"
    data_length = len(data)
    #socket.send(str.encode(json.dumps({"dataLength": data_length})))
    while len(data) >= 1:
        if len(data) <= 1024:
            socket.send(str.encode(data))
            data = ""
        else:
            socket.send(str.encode(data[:1024]))
            data = data[1024:]
