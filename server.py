# server.py
import time
import socket
import threading
import json

import copy

import network
import objects
from update import Updater, playerDefeat

gameData = {"players": {}, "executionTimes": [], "gridData": {}, "waitingToStart": True, "scores": {"pacteam": 0, "ghostteam": 0}, "isGameFinished": False}
"""
	gameData est un dictionnaire contenant :

		- "Players" qui désigne un dictionnaire contenant les id (ip + port) des joueurs:
			- chaque id désigne un dictionnaire contenant :
				-inputs[x,y]
				-speed[x,y]
				-position[x,y]
				-idleMove : booléen qui stocke si le joueur est arrêté
"""
gridUpdates = []
gridUpdatesCount = 0

connectedClients = []
clientsocketsList = []


def run_all(server, dt):
    global gridUpdates
    if gameData["waitingToStart"]:
        if "players" in gameData:
            numberOfPlayersReady = 0
            for player in gameData["players"]:
                if gameData["players"][player]["isReady"]:
                    numberOfPlayersReady += 1
            if numberOfPlayersReady == len(gameData["players"]) and numberOfPlayersReady >= 1:
                gameData["waitingToStart"] = False
                gameData["isGameFinished"] = False
                gameData["scores"]["pacteam"] = 0
                gameData["scores"]["ghostteam"] = 0
                for player in gameData["players"]:
                    gameData["players"][player]["score"] = 0

    else:
        safeData = copy.deepcopy(gameData)
        gridChanges = []
        for player in safeData['players']:
            updater = Updater(player, dt, dt)
            gameData["players"][player], gridChange = updater.run(safeData["players"][player], server.getGame())
            if gridChange is not None:
                gridChanges.append(gridChange)
        safeData = copy.deepcopy(gameData)
        gameData["players"] = playerDefeat(safeData["players"])
        gameData["gumCount"] = server.getGumCount()
        if gameData["gumCount"] == 0:
            gameData["waitingToStart"] = True
            gameData["isGameFinished"] = True
            gridUpdates.clear()
            gridChanges.clear()
            server.reloadGrid()
            for player in gameData["players"]:
                if gameData["players"][player]["isPacman"]:
                    gameData["scores"]["pacteam"] += gameData["players"][player]["score"]
                else:
                    gameData["scores"]["ghostteam"] += gameData["players"][player]["score"]
                gameData["players"][player]["isReady"] = False
                gameData["players"][player]["speed"] = [0, 0]
                gameData["players"][player]["inputs"] = [0, 0]
                gameData["players"][player]["idleMove"] = True
                gameData["players"][player]["respawn"] = True
        return gridChanges
    return []



class ServerThread():

    def __init__(self):
        self.game = objects.Game(0, 0, "level.json")
        self.game.loadGridData()

    def getGumCount(self):
        return self.game.countGum()

    def reloadGrid(self):
        self.game.loadGridData()

    def getGridData(self):
        return self.game.getGridData()

    def updateBlock(self, x, y, isPath, isGum, isSuperGum):
        self.game.updateBlock(x, y, isPath, isGum, isSuperGum)

    def getBlock(self, x, y):
        return self.game.getBlock(x, y)

    def draw(self, draw):
        self.game.draw(draw)
    def getGame(self):
        return self.game


class ClientThread():

    def __init__(self, ip, port, clientsocket, server):
        self.ip = ip
        self.port = port
        self.id = self.ip + ":" + str(self.port)
        self.username = "unknown"
        self.clientsocket = clientsocket
        print("[+] Nouveau thread pour %s %s" % (self.ip, self.port,))
        if self.id in gameData["players"]:
            self.position = gameData["players"][self.id]
        self.speed = [0.0, 0.0]
        self.time_speed = 0.5
        self.player_width = 1.0
        self.player_height = 1.0
        self.gameData = server.getGridData()
        self.div_x = self.gameData["dimensions"][0]
        self.div_y = self.gameData["dimensions"][0]
        self.position = [self.div_x / 2, self.div_y / 2]
        self.loaded_grid = False

        self.idle_move = True
        self.last_user_inputs = [0, 0]
        self.ready_to_recv = True
        self.ready_to_send = True

        self.is_editing = False

        self.total_changes_recv = 0

    def recv_data(self, clients_index):
        global gridUpdatesCount
        self.ready_to_recv = False
        r = self.clientsocket.recv(2048)
        data_str = r.decode("utf-8")
        data_str = data_str.split("end_of_data")[0]
        data_str = data_str[13:]
        if len(r) > 0:
            data = json.loads(data_str)
            self.total_changes_recv = data["changesLength"]
            if "isEditing" in data and data["isEditing"]:
                self.is_editing = True
                gridUpdates.append(data["gridChanges"])
                gridUpdatesCount += 1
                self.loaded_grid = data["loadedGrid"]
            elif not ("isMonitor" in data and data["isMonitor"]):
                self.username = data["username"]
                if not data["username"] in gameData["players"]:
                    self.add_player(data)
                gameData["players"][self.username]["inputs"] = data["inputs"]
                gameData["players"][self.username]["isPacman"] = data["isPacman"]
                gameData["players"][self.username]["isReady"] = data["isReady"]
                self.loaded_grid = data["loadedGrid"]
        else:
            print("Pas de données - Déconnecté du client")
            clientsocketsList.pop(clients_index)
            connectedClients.pop(clients_index)
            gameData["players"].pop(self.username)
        self.send_data(clients_index)
        self.ready_to_recv = True
        print("Received data : ", data_str)



    def send_data(self, clients_index):
        global gridUpdatesCount
        self.ready_to_send = False
        gameData["gridData"] = server.getGridData()
        clientData = copy.deepcopy(gameData)
        if self.loaded_grid:
            clientData.pop("gridData")
        if not gameData["waitingToStart"] or self.is_editing:
            clientData["gridUpdates"] = copy.deepcopy(gridUpdates)
        clientData["lastUpdate"] = gridUpdatesCount
        network.send_data(json.dumps(clientData), self.clientsocket)
        self.ready_to_send = True
        print("Sent data : ", clientData)


    def run(self, clients_index):
        """
        Lit les imputs du client, execute compute_pos et met à jour ses coordonnées
        """
        self.ready = False
        start_time = time.time()
        r = self.clientsocket.recv(2048)
        # print("Données reçues : ", r)
        if len(r) > 0:
            data = json.loads(r)
            if "isMonitor" in data and data["isMonitor"]:
                gameData["gridData"] = server.getGridData()
                self.clientsocket.send(str.encode(json.dumps(gameData)))
            else:
                self.username = data["username"]
                if not data["username"] in gameData["players"]:
                    self.add_player(data)
                gameData["players"][self.username]["inputs"] = data["inputs"]
                gameData["players"][self.username]["isPacman"] = data["isPacman"]
                gameData["gridData"] = server.getGridData()
                clientData = copy.deepcopy(gameData)
                if data["loadedGrid"]:
                    clientData.pop("gridData")
                clientData["gridUpdates"] = copy.deepcopy(gridUpdates)
                network.send_data(json.dumps(clientData), self.clientsocket)
                gameData["players"][self.username]["executionTime"] = time.time() - start_time
        else:
            print("Pas de données - Déconnecté du client")
            clientsocketsList.pop(clients_index)
            connectedClients.pop(clients_index)
        self.ready = True

    def get_total_changes_recv(self):
        return self.total_changes_recv

    def is_ready_to_send(self):
        return self.ready_to_send

    def is_ready_to_recv(self):
        return self.ready_to_recv

    def add_player(self, data):
        gameData["players"][self.username] = {"inputs": [0, 0], "position": [self.gameData["dimensions"][0]/2, self.gameData["dimensions"][1]/2],
                                       "speed": [0, 0], "idleMove": True, "respawn": True, "isSuper": False, "hasEaten": False, "isEscaping": False, "coolDown": 0,
                                              "isReady": False, "score": 0}



tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# tcpsock.bind(("", 25565))


tcpsock.bind(("", 32768))


# DO NOT FORGET TO CHANGE PORT

def accept_connection():
    while True:
        tcpsock.listen(10)
        print("En écoute...")
        (clientsocket, (ip, port)) = tcpsock.accept()
        clientsocketsList.append((ip, port, clientsocket))


d = threading.Thread(name='daemon', target=accept_connection)
d.setDaemon(True)
d.start()

server = ServerThread()

clientThreads = []

def server_run(dt):
    """
    Ajoute tout nouveau client à la liste des clients connectés puis, dans un thread séparé, execute run pour chaque client

    entrée: dt = temps entre la précédente exécution de la fonction et l'actuelle

    sortie: ne retourne rien
    """
    """
    for clientThread in clientThreads:
        clientThread.join()
        clientThreads.remove(clientThread)
    """
    global gridUpdatesCount
    global gridUpdates
    #Stockage des temps d'exécution
    gameData["executionTimes"].append(dt)
    if len(gameData["executionTimes"]) > 200:
        gameData["executionTimes"].pop(0)

    print("Delta time : ", dt)


    if len(clientsocketsList) > len(connectedClients):
        newthread = ClientThread(clientsocketsList[-1][0], clientsocketsList[-1][1], clientsocketsList[-1][2], server)
        connectedClients.append(newthread)
    index = 0
    changesRecv = []
    for client in connectedClients:
        changesRecv.append(client.get_total_changes_recv())
        if client.is_ready_to_recv():
            clientRecvThread = threading.Thread(name='daemon-client', target=client.recv_data, args=(index,))
            clientRecvThread.setDaemon(True)
            clientRecvThread.start()
            #clientThreads.append(clientThread)
            """
        if client.is_ready_to_send():
            clientSendThread = threading.Thread(name='daemon-client', target=client.send_data, args=(index,))
            clientSendThread.setDaemon(True)
            clientSendThread.start()
            #clientThreads.append(clientThread)
            """

        index += 1

    gridChanges = run_all(server, dt)
    if len(gridChanges) > 0:
        gridUpdates.append(gridChanges)
        gridUpdatesCount += 1
    for gridChange in gridUpdates:
        server.getGame().setGridChanges(gridChange)

    if len(changesRecv) > 0:
        print("Total grid updates : ", gridUpdatesCount, ", changes received : ", min(changesRecv), ", grid updates buffer : ", len(gridUpdates))
    if len(changesRecv) > 0 and gridUpdatesCount - min(changesRecv) < len(gridUpdates):
        print("Reducing buffer size, removing ", len(gridUpdates) - (gridUpdatesCount - min(changesRecv)),  " updates")
        gridUpdates = gridUpdates[len(gridUpdates) - (gridUpdatesCount - min(changesRecv)):]


delta_time = 0
while True:
    before_time = time.time()
    server_run(delta_time)
    after_time = time.time()
    delta_time = after_time - before_time
