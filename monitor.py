# monitor.py
# librairie graphique utilisée : https://pyglet.readthedocs.io/en/latest/programming_guide/quickstart.html
import pyglet
import socket
import json
import display
# Key game Press
from pyglet.window import key
from pyglet.window import mouse

import editor
import objects

# Connection to server
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect(("localhost", 32768))

# Display config
width = 1280
height = 720

window = pyglet.window.Window(width, height)
draw = display.Draw(width, height, window)


class GameMonitor():
    """
    Classe utilisée par le moniteur afin de garder en mémoire les variables susceptibles d'être accédées fréquemment.
    À l'avenir on peut envisager plusieurs sous-classes afin de rendre la chose plus propre.
    """

    def __init__(self):
        """
        On initialise le menu principal et les variables nécessaires au bon fonctionnement du client.
        """

        self.move_inputs = [0, 0]

        self.play = "Jouer"
        self.editor = "Editeur de niveaux"
        self.parameters = "Paramètres"
        self.main_menu = "Menu principal"

        self.mainMenu = draw.Menu(width / 4, height / 4, width / 2, height / 2, "NamCap", 20)
        self.mainMenu.addButton(self.play)
        self.mainMenu.addButton(self.editor)
        self.mainMenu.addButton(self.parameters)
        self.state = self.play

        self.div_x = 28
        self.div_y = 28

        self.game = objects.Game(self.div_x, self.div_y, "level.json")

        self.socket = None
        self.start_game()
        origin_x, origin_y, view_width, view_height, block_size = draw.define_viewport(self.div_x, self.div_y, True)
        self.editor_instance = editor.Editor(block_size, origin_x, origin_y, view_width, view_height, self.div_x,
                                             self.div_y)

        draw.set_viewport(self.div_x, self.div_y, True)

    def send_inputs(self):
        """
        Sert à envoyer les entrées du client sous forme dans un premier temps, de dictionnaire converti en chaîne de caractères qui sera elle même convertie en bytes, au serveur
        """
        Data = {"inputs": self.move_inputs, "loadedGrid": False, "isMonitor": True}
        data_str = json.dumps(Data)
        self.socket.send(str.encode(data_str))

    # Called by window event
    def on_key_press(self, symbol, modifiers):
        """
        Sauvegarde le déplacement dans une liste propre à la fonction. Cette fonction est appelée lors d'un évènement spécifique clavier détecté par Pyglet.
        """
        if symbol == key.Z or symbol == key.UP:
            self.move_inputs[1] += 1
            print('"Z" or "Up" key pressed. Go forward')
        elif symbol == key.S or symbol == key.DOWN:
            self.move_inputs[1] -= 1
            print('"S" or "Down" key pressed. Go back')
        elif symbol == key.D or symbol == key.RIGHT:
            self.move_inputs[0] += 1
            print('"D" or "Right" key pressed. Go on the right')
        elif symbol == key.Q or symbol == key.LEFT:
            self.move_inputs[0] -= 1
            print('"Q" or "Left" key pressed. Go on the left')

    # Key game Release
    # Called by window event
    def on_key_release(self, symbol, modifiers):
        """
        Sauvegarde le déplacement dans une liste propre à la fonction. Cette fonction est appelée lors d'un évènement spécifique clavier détecté par Pyglet.
        """
        if symbol == key.Z or symbol == key.UP:
            if self.move_inputs[1] >= 1:
                self.move_inputs[1] = 0
                print('"Z" or "Up" key released. Stop going forward')
        elif symbol == key.S or symbol == key.DOWN:
            if self.move_inputs[1] <= -1:
                self.move_inputs[1] = 0
                print('"S" or "Down" key released. Stop going back')
        elif symbol == key.D or symbol == key.RIGHT:
            if self.move_inputs[0] >= 1:
                self.move_inputs[0] = 0
                print('"D" or "Right" key released. Stop going on the right')
        elif symbol == key.Q or symbol == key.LEFT:
            if self.move_inputs[0] <= -1:
                self.move_inputs[0] = 0
                print('"Q" or "Left" key released. Stop going on the left')

    def recv_data_and_display(self):
        """
        Récupère et affiche directement les données envoyées par le serveur. Conversion d'un string reçu en JSON.
        """

        r = self.socket.recv(2048 * 128)
        data = json.loads(r)
        if "gridData" in data:
            self.game.setGridData(data["gridData"])
        draw.clear()
        self.game.draw(draw)
        draw.draw_players(data)
        draw.draw_side_rect()
        draw.server_info(data.copy())

    def menu_selection(self, x, y):
        """
        Sélection d'une fonctionnalité à lancer dans le menu principal
        """

        if self.state == self.main_menu:
            selection = self.mainMenu.checkForClick([x, y])
            if selection == self.play:
                self.start_game()
            if selection == self.editor:
                self.start_editor()
            if selection == self.parameters:
                self.start_parameters()
        if self.state == self.editor:
            self.editor_instance.on_click(x, y)

    def start_game(self):
        """
        Établissement de la connexion avec le serveur.
        """
        self.state = self.play
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("134.122.101.40", 32768))

    def start_editor(self):
        self.state = self.editor

    def start_parameters(self):
        self.state = self.parameters

    def main_loop(self):
        """
        Sert à afficher les fonctionnalités du jeu en fonction de là où se trouve le client
        """
        if self.state == self.main_menu:
            draw.draw_menu(self.mainMenu)
        elif self.state == self.play:
            self.send_inputs()
            self.recv_data_and_display()
        elif self.state == self.editor:
            self.editor_instance.on_draw(draw)
        else:
            draw.clear()


monitor = GameMonitor()


@window.event
def on_key_press(symbol, modifiers):
    monitor.on_key_press(symbol, modifiers)


@window.event
def on_key_release(symbol, modifiers):
    monitor.on_key_release(symbol, modifiers)


@window.event
def on_mouse_press(x, y, button, modifiers):
    if button == mouse.LEFT:
        monitor.menu_selection(x, y)


def on_draw(dt):
    monitor.main_loop()

    # client.send_inputs()
    # client.recv_data_and_display()


pyglet.clock.schedule_interval(on_draw, interval=1 / 120)
pyglet.app.run()