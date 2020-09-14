# client.py
# librairie graphique utilisée : https://pyglet.readthedocs.io/en/latest/programming_guide/quickstart.html
import pyglet
import socket
import json
# Key game Press
from pyglet.window import key
from pyglet.window import mouse

import threading
import copy
import time

import display
import editor
import objects
from update import Updater

# Connection to server
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect(("localhost", 32768))

# Display config
width = 1280
height = 720
"""
Ici sont définies les dimensions de la fenêtre.
"""
window = pyglet.window.Window(width, height, resizable=True)
draw = display.Draw(width, height, window, False, 28, 28)

pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)

def loadConfig():
    with open("config.json", "r") as text_file:
        return json.loads(text_file.read())

def saveConfig(data):
    with open("config.json", "w") as text_file:
        text_file.write(json.dumps(data))

class GameClient():
    """
    Classe utilisée par le client afin de garder en mémoire les variables susceptibles d'être accédées fréquemment.
    À l'avenir on peut envisager plusieurs sous-classes afin de rendre la chose plus propre.
    """

    def __init__(self):
        """
        On initialise le menu principal et les variables nécessaires au bon fonctionnement du client.
        """

        self.move_inputs = [0, 0]

        self.play = "Jouer"
        self.editor = "Editeur de niveaux"
        self.multiplayer_editor = "Editeur de niveaux multijoueur"
        self.parameters = "Paramètres"
        self.main_menu = "Menu principal"

        self.mainMenu = draw.Menu(1 / 4, 1 / 4, 1 / 2, 1 / 2, "NamCap", 20/height)
        self.mainMenu.addButton(self.play)
        self.mainMenu.addButton(self.editor)
        self.mainMenu.addButton(self.multiplayer_editor)
        self.mainMenu.addButton(self.parameters)
        self.state = self.main_menu

        self.div_x = 28
        self.div_y = 28
        self.width = width
        self.height = height

        self.game = objects.Game(self.div_x, self.div_y, "level.json")
        try:
            self.client_config = loadConfig()
        except:
            self.client_config = {"username": "undefined", "isPacman": False, "serverIP": "localhost", "serverPort": 32768}
            saveConfig(self.client_config)

        self.socket = None
        self.can_send = True
        self.can_receive = True

        origin_x, origin_y, view_width, view_height, block_size = draw.define_viewport(self.div_x, self.div_y, True)
        self.editor_instance = editor.Editor(block_size, origin_x, origin_y, view_width, view_height, self.div_x,
                                             self.div_y)
        self.multiplayer_editor_instance = editor.MultiplayerEditor(block_size, origin_x, origin_y, view_width,
                                                                                    view_height, self.div_x, self.div_y)
        self.client_edition_changes = []

        draw.set_viewport(self.div_x, self.div_y, True)
        self.gameData = {}
        self.last_input_change_time = time.time()

        self.ready_change = False
        self.viewing_scores = False

        self.is_fullscreen = False

        self.changes_length = 0

        self.parameters_instance = display.Parameters({"Pseudo": self.client_config["username"], "IP du serveur": self.client_config["serverIP"], "Port du serveur": self.client_config["serverPort"]})

    def update_viewport(self, width, height):
        draw.on_resize(width, height, False, self.game.get_grid_width(), self.game.get_grid_height())
        if self.state == self.editor:
            self.editor_instance.on_resize(width, height, draw)
        if self.state == self.multiplayer_editor:
            self.multiplayer_editor_instance.on_resize(width, height, draw)
        self.width = width
        self.height = height

    def run_all(self, dt):
        input_delta_time = time.time() - self.last_input_change_time
        if "executionTimes" in self.gameData:
            if self.gameData["executionTimes"][-1] != 0:
                loops = dt / self.gameData["executionTimes"][-1]
            else:
                loops = 1
            print("Client delta time : ", dt, " server last delta time :", self.gameData["executionTimes"][-1], " loops to do : ", loops)
        else:
            loops = 1
        for i in range(round(loops)):
            if "players" in self.gameData:
                safeData = copy.deepcopy(self.gameData)
                for player in safeData['players']:
                    updater = Updater(player, self.gameData["executionTimes"][-1], self.gameData["executionTimes"][-1])
                    self.gameData["players"][player], gridChange = updater.run(safeData["players"][player], self.game)

    def send_inputs(self):
        """
        Sert à envoyer les entrées du client sous forme dans un premier temps, de dictionnaire converti en chaîne de caractères qui sera elle même convertie en bytes, au serveur.
        """
        if self.state == self.multiplayer_editor:
            Data = {"changesLength": self.changes_length, "isEditing": True, "gridChanges": copy.deepcopy(self.client_edition_changes), "loadedGrid": self.multiplayer_editor_instance.is_grid_loaded(), "username": self.client_config["username"]}
            self.client_edition_changes.clear()
        else:
            Data = {"changesLength": self.changes_length, "inputs": self.move_inputs, "loadedGrid": self.game.is_loaded_grid(), "username": self.client_config["username"], "isPacman": self.client_config["isPacman"], "isReady": self.client_config["isReady"]}
        data_str = json.dumps(Data)
        data_str = "start_of_data" + data_str + "end_of_data"
        self.socket.send(str.encode(data_str))

    # Called by window event
    def on_key_press(self, symbol, modifiers):
        """
        Pour lorsqu'on appuie sur une touche de déplacement :
        Sauvegarde le déplacement dans une liste propre à la fonction. Cette fonction est appelée lors d'un évènement spécifique du clavier détecté par Pyglet.
        """
        if symbol == key.Z or symbol == key.UP:
            self.move_inputs[1] += 1
            self.last_input_change_time = time.time()
        elif symbol == key.S or symbol == key.DOWN:
            self.move_inputs[1] -= 1
            self.last_input_change_time = time.time()
        elif symbol == key.D or symbol == key.RIGHT:
            self.move_inputs[0] += 1
            self.last_input_change_time = time.time()
        elif symbol == key.Q or symbol == key.LEFT:
            self.move_inputs[0] -= 1
            self.last_input_change_time = time.time()
        elif symbol == key.F11:
            if self.is_fullscreen:
                self.is_fullscreen = False
                window.set_fullscreen(False)
            else:
                self.is_fullscreen = True
                window.set_fullscreen(True)
        elif symbol == key.BACKSPACE:
            self.on_text("", True)

    # Key game Release
    # Called by window event
    def on_key_release(self, symbol, modifiers):
        """
        Pour lorsqu'on relâche une touche de déplacement :
        Sauvegarde le déplacement dans une liste propre à la fonction. Cette fonction est appelée lors d'un évènement spécifique clavier détecté par Pyglet.
        """
        if symbol == key.Z or symbol == key.UP:
            if self.move_inputs[1] >= 1:
                self.move_inputs[1] = 0
                self.last_input_change_time = time.time()
        elif symbol == key.S or symbol == key.DOWN:
            if self.move_inputs[1] <= -1:
                self.move_inputs[1] = 0
                self.last_input_change_time = time.time()
        elif symbol == key.D or symbol == key.RIGHT:
            if self.move_inputs[0] >= 1:
                self.move_inputs[0] = 0
                self.last_input_change_time = time.time()
        elif symbol == key.Q or symbol == key.LEFT:
            if self.move_inputs[0] <= -1:
                self.move_inputs[0] = 0
                self.last_input_change_time = time.time()

    def on_text(self, text, hasToDelete):
        if self.state == self.parameters:
            self.parameters_instance.on_text(text, hasToDelete)
        if self.state == self.editor:
            self.editor_instance.on_text(text, hasToDelete)
        if self.state == self.multiplayer_editor:
            self.multiplayer_editor_instance.on_text(text, hasToDelete)

    def recv_data(self):
        """
        Récupère les données envoyées par le serveur. Conversion d'un string reçu en JSON.
        """
        """
        r = None
        while r is None:
            r = self.socket.recv(256)
            print("Data received :", r)
        try:
            data_info = json.loads(r)
        except:
            print("Can't parse data received")
            r = self.socket.recv(1024*100)
            print("Data received :", r)
            print("Exiting loop")
            return None
        print(data_info)
        data_str = ""
        while len(data_str) < data_info["dataLength"]:
            r = None
            while r is None:
                r = self.socket.recv(1024)
            print("Received packet, data length recv : ", len(data_str), "of", data_info["dataLength"], " packet's length is : ", len(r.decode("utf-8")))
            data_str += r.decode("utf-8")
        data = json.loads(data_str)
        """
        data_str = ""
        data_read = False
        while data_str[:13] != "start_of_data":
            r = self.socket.recv(1024)
            data_str = r.decode("utf-8")
        data_str = data_str[13:]
        data_packs = 1
        while not data_read:
            data_packs += 1
            r = self.socket.recv(1024)
            data_recv = r.decode("utf-8")
            data_str += data_recv
            if data_str.find("end_of_data") != -1:
                data_read = True

        data_str = data_str.split("end_of_data")[0]

        try:
            data = json.loads(data_str)
        except:
            print("Error parsing json")
            return None
        if self.state == self.multiplayer_editor:
            if "gridData" in data:
                self.multiplayer_editor_instance.set_grid_data(data["gridData"])
                self.multiplayer_editor_instance.set_grid_size(data["gridData"]["dimensions"][0], data["gridData"]["dimensions"][1])
                self.multiplayer_editor_instance.on_grid_resize(draw)
            if "gridUpdates" in data:
                self.multiplayer_editor_instance.set_grid_changes(data["gridUpdates"])

        else:
            if "gridData" in data:
                self.game.setGridData(data["gridData"])
                draw.on_grid_resize(data["gridData"]["dimensions"][0], data["gridData"]["dimensions"][1])
            if "gridUpdates" in data:
                self.game.updateGrid(data["gridUpdates"])
        if "lastUpdate" in data:
            self.changes_length = data["lastUpdate"]
        self.gameData = data

    def display(self):
        draw.clear()
        if "waitingToStart" in self.gameData and self.gameData["waitingToStart"]:
            if self.viewing_scores:
                draw.score_screen(self.gameData, self.client_config["username"])
            else:
                draw.waiting_screen(self.gameData, self.client_config["username"])
        else:
            self.game.draw(draw)
            if "players" in self.gameData:
                draw.draw_players(copy.deepcopy(self.gameData))
            draw.draw_side_rect()

    def mouse_release(self, x, y):
        x = x / self.width
        y = y / self.height
        if self.state == self.editor:
            self.editor_instance.on_click_release()
        if self.state == self.multiplayer_editor:
            self.multiplayer_editor_instance.on_click_release()

    def mouse_motion(self, x, y):
        x = x/self.width
        y = y/self.height
        if self.state == self.editor:
            self.editor_instance.on_click_motion(x, y)
        if self.state == self.multiplayer_editor:
            self.multiplayer_editor_instance.on_click_motion(x, y)

    def menu_selection(self, x, y):
        """
        Sélection d'une fonctionnalité à lancer dans le menu principal.
        """
        if self.state == self.play:
            if self.gameData["waitingToStart"]:
                if self.viewing_scores:
                    self.viewing_scores = draw.interact_score_screen(x, y)
                else:
                    chosen_pacman, isReady = draw.interact_waiting_screen(x, y)
                    if chosen_pacman is not None:
                        self.client_config["isPacman"] = chosen_pacman
                    if isReady is not None:
                        if "isReady" in self.client_config and self.client_config["isReady"]:
                            self.client_config["isReady"] = False
                        else:
                            self.client_config["isReady"] = True
        x = x/self.width
        y = y/self.height
        if self.state == self.main_menu:
            selection = self.mainMenu.checkForClick([x, y])
            if selection == self.play:
                self.start_game()
            if selection == self.editor:
                self.start_editor()
            if selection == self.multiplayer_editor:
                self.start_multiplayer_editor()
            if selection == self.parameters:
                self.start_parameters()
            self.mainMenu.resetAllButtons()
        if self.state == self.editor:
            selection = self.editor_instance.on_click(x, y)
            if selection is not None and selection:
                self.state = self.main_menu
        if self.state == self.multiplayer_editor:
            selection = self.multiplayer_editor_instance.on_click(x, y)
            if selection is not None and selection is True:
                self.state = self.main_menu
            if selection is not None and type(selection) is dict:
                self.client_edition_changes.append(selection)
        if self.state == self.parameters:
            value = self.parameters_instance.on_click(x, y)
            if value is not None:
                self.state = self.main_menu
                self.client_config = {"username": value["Pseudo"], "serverIP": value["IP du serveur"], "serverPort": int(value["Port du serveur"]), "isPacman": self.client_config["isPacman"]}
                saveConfig(self.client_config)


    def start_game(self):
        """
        Établissement de la connexion avec le serveur.
        """
        self.state = self.play
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.client_config["serverIP"], self.client_config["serverPort"]))

    def start_editor(self):
        """
        Fait apparaître l'éditeur de niveaux lorsqu'on le sélectionne.
        """
        self.state = self.editor
        self.editor_instance.on_resize(draw.getWidth(), draw.getHeight(), draw)

    def start_multiplayer_editor(self):
        self.state = self.multiplayer_editor
        self.multiplayer_editor_instance.on_resize(draw.getWidth(), draw.getHeight(), draw)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.client_config["serverIP"], self.client_config["serverPort"]))

    def start_parameters(self):
        """
        Fait apparaître les paramètres lorsqu'on les sélectionne.
        """
        self.state = self.parameters

    def send_data_thread(self):
        self.can_send = False
        try:
            self.send_inputs()
        except:
            print("Network error : cant send data, perhaps connection is reset")
            print("New connection attempt...")
            try:
                self.socket.connect((self.client_config["serverIP"], self.client_config["serverPort"]))
            except:
                print("Network error : cant reconnect to the server")
        self.can_send = True


    def recv_data_thread(self):
        self.can_receive = False
        try:
            self.recv_data()
        except:
            print("Could not receive data")
        self.can_receive = True

    def main_loop(self, dt):
        """
        Sert à afficher les fonctionnalités du jeu en fonction de là où se trouve le client.
        """
        if self.state == self.main_menu:
            draw.draw_bckg_rect()
            draw.draw_menu(self.mainMenu)
        elif self.state == self.play:
            if "waitingToStart" in self.gameData and self.gameData["waitingToStart"]:
                self.game.reverseChanges()
            if "waitingToStart" in self.gameData and self.gameData["waitingToStart"] and not self.ready_change:
                self.client_config["isReady"] = False
                self.ready_change = True
                if "isGameFinished" in self.gameData and self.gameData["isGameFinished"]:
                    self.viewing_scores = True
            if "waitingToStart" in self.gameData and not self.gameData["waitingToStart"]:
                self.ready_change = False
                self.client_config["isReady"] = False
            if "isReady" in self.client_config:
                print("Ready state :", self.client_config["isReady"])
            if self.can_send:
                sendThread = threading.Thread(name='daemon-client', target=self.send_data_thread)
                sendThread.setDaemon(True)
                sendThread.start()
            if self.can_receive:
                recvThread = threading.Thread(name='daemon-client', target=self.recv_data_thread)
                recvThread.setDaemon(True)
                recvThread.start()

            self.display()
            self.run_all(dt)
        elif self.state == self.editor:
            self.editor_instance.on_draw(draw)
        elif self.state == self.multiplayer_editor:
            self.multiplayer_editor_instance.on_draw(draw)
            if "players" in self.gameData:
                draw.draw_players(self.gameData)
            if self.can_send:
                sendThread = threading.Thread(name='daemon-client', target=self.send_data_thread)
                sendThread.setDaemon(True)
                sendThread.start()
            if self.can_receive:
                recvThread = threading.Thread(name='daemon-client', target=self.recv_data_thread)
                recvThread.setDaemon(True)
                recvThread.start()
        elif self.state == self.parameters:
            draw.draw_bckg_rect()
            self.parameters_instance.draw(draw.rect, draw.centered_text, draw.getWidth(), draw.getHeight())
        else:
            draw.clear()


client = GameClient()

@window.event
def on_key_press(symbol, modifiers):
    client.on_key_press(symbol, modifiers)


@window.event
def on_key_release(symbol, modifiers):
    client.on_key_release(symbol, modifiers)


@window.event
def on_mouse_press(x, y, button, modifiers):
    if button == mouse.LEFT:
        client.menu_selection(x, y)

@window.event
def on_mouse_release(x, y, button, modifiers):
    if button == mouse.LEFT:
        client.mouse_release(x, y)

@window.event
def on_mouse_motion(x, y, dx, dy):
    client.mouse_motion(x, y)
@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    client.mouse_motion(x, y)


@window.event
def on_resize(width, height):
    client.update_viewport(width, height)

@window.event
def on_text(text):
    client.on_text(text, False)

def on_draw(dt):
    client.main_loop(dt)

    # client.send_inputs()
    # client.recv_data_and_display()


pyglet.clock.schedule_interval(on_draw, interval=1 / 120)
pyglet.app.run()