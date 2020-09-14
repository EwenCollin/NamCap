# display.py
# Contains all functions and stores data for display for both client and server
import pyglet
import copy

class Parameters():

    def __init__(self, valueDict):
        self.initial_values = copy.deepcopy(valueDict)
        self.changing_value = ""
        self.text = "Changer"
        self.restore = "Restaurer"
        self.back = "Retour"
        self.values = copy.deepcopy(valueDict)
        self.back_menu = Draw.Menu(0, 0, 0.25, 0.5, "Paramètres", 0.02)
        self.back_menu.addButton(self.restore)
        self.back_menu.addButton(self.back)
        y = 0
        data_length = len(self.values)
        for value in self.values:
            self.values[value] = {"value": str(self.values[value]), "menu": Draw.Menu(0.25, (data_length - 1 - y)/data_length, 0.5, 0.75/data_length, value + " : " + str(self.values[value]), 0.02)}
            self.values[value]["menu"].addButton(self.text)
            y += 1

    def draw(self, rect, centered_text, width, height):
        self.back_menu.draw(rect, centered_text, width, height)
        for value in self.values:
            self.values[value]["menu"].draw(rect, centered_text, width, height)

    def get_values(self):
        outputValues = {}
        for value in self.values:
            outputValues[value] = self.values[value]["value"]
        return outputValues

    def on_click(self, x, y):
        self.changing_value = ""
        self.back_menu.resetAllButtons()
        side_menu = self.back_menu.checkForClick([x, y])
        if side_menu is not None:
            if side_menu == self.restore:
                self.__init__(self.initial_values)
            elif side_menu == self.back:
                return self.get_values()

        for value in self.values:
            self.values[value]["menu"].resetAllButtons()
        for value in self.values:
            click = self.values[value]["menu"].checkForClick([x, y])
            if click is not None and click == self.text:
                self.changing_value = value
        return None



    def on_text(self, text, hasToDelete):
        if self.changing_value in self.values:
            if hasToDelete:
                self.values[self.changing_value]["value"] = self.values[self.changing_value]["value"][:-1]
            else:
                self.values[self.changing_value]["value"] += text
            self.values[self.changing_value]["menu"].updateTitle(self.changing_value + " : " + self.values[self.changing_value]["value"])








class Draw():
    """
    Main class for display, contains all the functions needed to display the game correctly.
    Most of the functions are used for display, some like in the inner class Menu are used to know were the user clicked.
    """

    def __init__(self, width, height, window, side, div_x, div_y):
        self.width = width
        self.height = height
        self.font = 'Verdana'
        self.window = window
        self.div_x, self.div_y = div_x, div_y
        self.isSidedRight = side
        self.origin_x, self.origin_y, self.view_width, self.view_height, self.unit = self.define_viewport(self.div_x,
                                                                                                          self.div_y,
                                                                                                          self.isSidedRight)

        self.player_width = self.unit
        self.player_height = self.unit
        self.side_color = (60, 60, 60)
        self.bckg_color = (40, 40, 40)

    def getWidth(self):
        return self.width

    def getHeight(self):
        return self.height

    def draw_bckg_rect(self):
        self.rect(0, 0, self.width, self.height, self.bckg_color)

    def on_resize(self, width, height, side, div_x, div_y):
        self.__init__(width, height, self.window, side, div_x, div_y)

    def on_grid_resize(self, div_x, div_y):
        self.div_x = div_x
        self.div_y = div_y
        self.origin_x, self.origin_y, self.view_width, self.view_height, self.unit = self.define_viewport(self.div_x,
                                                                                                          self.div_y,
                                                                                                          self.isSidedRight)
    def get_block_size(self):
        return self.unit

    def set_viewport(self, width, height, isSidedRight):
        self.isSidedRight = isSidedRight
        self.origin_x, self.origin_y, self.view_width, self.view_height, self.unit = self.define_viewport(width, height,
                                                                                                          self.isSidedRight)

    def define_viewport(self, width, height, isSidedRight):
        """
        Définit la taille de l'écran de jeu selon les dimensions de la fenêtre.
        Permet de redimensionner la fenêtre.

        Entrée: width = la largeur de l'écran de jeu : INT
                height = la hauteur de l'écran de jeu : INT

        Sortie: coordonnée horizontale de l'origine de l'écran de jeu : FLOAT,
                coordonnée verticale de l'origine de l'écran de jeu : FLOAT,
                largeur de l'écran de jeu : FLOAT,
                hauteur de l'écran de jeu : FLOAT,
                ratio pixels d'écran / pixels ingame de la largeur : FLOAT.
        """
        view_width = self.width
        view_height = self.height
        if width / height > self.width / self.height:
            view_width = self.width
            view_height = (view_width / width) * height
        elif width / height < self.width / self.height:
            view_height = self.height
            view_width = (view_height / height) * width
        elif width / height == self.width / self.height:
            view_width = self.width
            view_height = self.height
        if isSidedRight:
            return (self.width - view_width), (
                    self.height - view_height), view_width, view_height, view_width / width
        return (self.width - view_width) / 2, (
                self.height - view_height) / 2, view_width, view_height, view_width / width

    def draw_players(self, gameData):
        """
        Affiche les joueurs.
        Si un joueur atteint le bord de l'écran, un clone sera aussi affiché de l'autre coté
        (n'aime pas les angles de l'écran)

        Entrée: gameData = le dictionnaire gameData téléchargé depuis le server.
        """
        pacman_super = False
        for player in gameData["players"]:
            if gameData["players"][player]["isSuper"]:
                pacman_super = True
        color = (255, 20, 255)
        for player in gameData["players"]:
            if gameData["players"][player]["isPacman"]:
                color = (255, 255, 20)
            else:
                if pacman_super:
                    color = (20, 20, 190)
                else:
                    color = (255, 20, 20)
            if gameData["players"][player]["isEscaping"]:
                color = (80, 80, 80)
            position = gameData["players"][player]["position"]
            position[0] = position[0] * self.unit + self.origin_x
            position[1] = position[1] * self.unit + self.origin_y

            self.rect(position[0], position[1], self.player_width, self.player_height, color)
            self.text(player, position[0], position[1] + self.player_height + 2, 24)

            clone_pos = [position[0], position[1]]
            if position[0] + self.player_width > self.view_width:
                clone_pos[0] = position[0] - self.view_width
            if position[0] < self.origin_x:
                clone_pos[0] = position[0] + self.view_width
            if position[1] + self.player_height > self.view_height:
                clone_pos[1] = position[1] - self.view_height
            if position[1] < self.origin_y:
                clone_pos[1] = position[1] + self.view_height

            if clone_pos[0] != position[0] or clone_pos[1] != position[0]:
                self.rect(clone_pos[0], clone_pos[1], self.player_width, self.player_height, color)
                self.text(player, clone_pos[0], clone_pos[1] + self.player_height + 2, 24)

    def draw_game(self, gameData):
        """
        Se charge de l'affichage du jeu :
        -efface l'écran
        -affiche les joueurs
        -affiche les bordures d'écran en gris

        Entrée: gameData = dictionnaire /!\ doit être téléchargé depuis le server avant d'être utilisé
                                            Se référer à namcap server pour la structure précise de gameData

        Sortie: ne retourne rien
        """
        self.clear()
        self.draw_players(gameData)
        self.draw_side_rect()

    def draw_side_rect(self):
        self.rect(0, 0, self.origin_x, self.height, self.side_color)
        self.rect(self.origin_x + self.view_width, 0, self.width - self.origin_x - self.view_width, self.height,
                  self.side_color)
        self.rect(0, 0, self.width, self.origin_y, self.side_color)
        self.rect(0, self.origin_y + self.view_height, self.width, self.height - self.view_height - self.origin_y,
                  self.side_color)

    def clear(self):
        """
        Efface l'écran.
        """
        self.window.clear()

    def rect_in_viewport(self, x, y, w, h, color):
        self.rect(x + self.origin_x, y + self.origin_y, w, h, color)

    def rect(self, x, y, w, h, color):
        """
        dessine un rectangle

        entrée: x = coordonnée horizontale (désigne la gauche du rectangle) : FLOAT
                y = coordonnée verticale (désigne le bas du rectangle) : FLOAT
                w = width, càd la largeur du rectangle : FLOAT
                h = height, càd la hauteur du rectangle : FLOAT
                color = couleur du rectangle : (INT, INT, INT)
        """
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2f', [x, y, x + w, y, x + w, y + h, x, y + h]),
                             ('c4B', (color[0], color[1], color[2], 255,  # color for point0
                                      color[0], color[1], color[2], 255,  # color for point1
                                      color[0], color[1], color[2], 255,  # color for point2
                                      color[0], color[1], color[2], 255)  # color for point3
                              )
                             )

    def text(self, text, x, y, size):
        """
        écrit un bout de texte (les coords correspondent au coin en bas à gauche)

        entrée: text = le texte (duh!) : STR
                x = coordonnée horizontale : FLOAT
                y = coordonnée verticale : FLOAT
                size = taille de la police
        """
        label = pyglet.text.Label(text,
                                  font_name=self.font,
                                  font_size=size,
                                  x=x, y=y)
        label.draw()

    def centered_text(self, text, x, y, size):
        """
        écrit un bout de texte (les coords correspondent au centre)

        entrée: text = le texte (duh!) : STR
                x = coordonnée horizontale : FLOAT
                y = coordonnée verticale : FLOAT
                size = taille de la police
        """
        label = pyglet.text.Label(text,
                                  font_name=self.font,
                                  font_size=size,
                                  x=x, y=y,
                                  anchor_x='center', anchor_y='center')
        label.draw()

    def draw_menu(self, menu):
        """
        Dessine le menu.
        """
        menu.draw(self.rect, self.centered_text, self.width, self.height)

    def server_info(self, info):
        y = self.height - 50
        self.centered_text("Infos du serveur", self.origin_x / 2, y, 20)
        y -= 50
        self.text("Joueurs connectés : " + str(len(info["players"])), 20, y, 15)
        y -= 35
        self.text("Joueurs : ", 20, y, 15)
        for player in info["players"]:
            y -= 30
            self.text(player + " - position : " + str(info["players"][player]["position"]), 40, y, 12)
            if "executionTime" in info["players"][player]:
                y -= 30
                self.text("Dernier temps de traitement : " + str(round(info["players"][player]["executionTime"]*1000, 4)) + " ms", 60, y, 12)
        y -= 35
        self.text("Performances (ms):", 20, y, 15)
        y -= 35
        self.graph(20, y - 120, self.origin_x - 40, 120, info["executionTimes"])

    def graph(self, origin_x, origin_y, width, height, data):
        x = 0
        max_data = max(data)
        if max_data == 0:
            max_data = 1/1000
        for info in data:
            x += 1
            self.rect(origin_x + x * width / len(data), origin_y, width/len(data), info*height/max_data, (40, 255, 60))
        self.text(str(round(max_data*1000)), origin_x, origin_y + height - 20, 12)
        self.text(str(round(max_data*1000/2)), origin_x, origin_y + height/2 - 20, 12)

    def waiting_screen(self, gameData, username):
        self.rect(0, 0, self.width, self.height, self.bckg_color)
        self.centered_text("Connecté au serveur", self.width / 2, 4.5*self.height/5, 25)
        self.centered_text("Choisissez votre équipe", self.width / 2, 4 * self.height / 5, 20)
        self.rect(self.width/4 - 1.5*self.width/10, 2 * self.height/5, 1.5*self.width/5, 1.5*self.height/5, (225, 205, 10))
        self.centered_text("PacTeam", self.width / 4, 5.5 * self.height / 10, 30)
        self.rect(3*self.width/4 - 1.5*self.width/10, 2 * self.height/5, 1.5*self.width/5, 1.5*self.height/5, (225, 10, 10))
        self.centered_text("GhostTeam", 3*self.width / 4, 5.5 * self.height / 10, 30)
        waiting_for_players = []
        for player in gameData["players"]:
            if not gameData["players"][player]["isReady"]:
                waiting_for_players.append(player)
        if username in gameData["players"]:
            if gameData["players"][username]["isReady"]:
                self.rect(self.width/4, 1.25 * self.height/5, self.width/2, 0.5*self.height/5, (10, 225, 10))
                self.centered_text("Je choisis encore", self.width/2, 1.5*self.height/5, 20)
            else:
                self.rect(self.width/4, 1.25 * self.height/5, self.width/2, 0.5*self.height/5, (225, 10, 10))
                self.centered_text("C'est parti !", self.width/2, 1.5*self.height/5, 20)
        self.centered_text("On attend les joueurs :", self.width / 2, 1 * self.height / 5, 15)
        y = 0
        for player in waiting_for_players:
            y += 20
            self.centered_text(player, self.width / 2, 1 * self.height / 5 - y, 12)

    def interact_waiting_screen(self, x, y):
        chosen_pacman = None
        isReady = None
        if self.width/4 - 1.5*self.width/10 < x < 1.5*self.width/5 + self.width/4 - 1.5*self.width/10 and 2 * self.height/5 < y < 2 * self.height/5 + 1.5*self.height / 5:
            chosen_pacman = True
        elif 3*self.width/4 - 1.5*self.width/10 < x < 1.5*self.width/5 + 3*self.width/4 - 1.5*self.width/10 and 2 * self.height/5 < y < 2 * self.height/5 + 1.5*self.height / 5:
            chosen_pacman = False
        elif self.width/4 < x < 3*self.width/4 and 1.25 * self.height/5 < y < 1.25 * self.height/5 + 0.5*self.height/5:
            isReady = True
        return chosen_pacman, isReady

    def score_screen(self, gameData, username):
        self.rect(0, 0, self.width, self.height, self.bckg_color)
        self.centered_text("Partie terminée", self.width / 2, 4.5*self.height/5, 25)
        self.centered_text("Scores des équipes", self.width / 2, 4 * self.height / 5, 20)
        self.rect(self.width/4 - 1.5*self.width/10, 1.30 * self.height/5, 1.5*self.width/5, 2.20*self.height/5, (225, 205, 10))
        self.centered_text("PacTeam", self.width / 4, 5.5 * self.height / 10, 30)
        self.centered_text(str(gameData["scores"]["pacteam"]), self.width / 4, 4.75 * self.height / 10, 25)
        y = 0
        for player in gameData["players"]:
            if gameData["players"][player]["isPacman"]:
                y += 40
                self.centered_text(player + " (" + str(gameData["players"][player]["score"]) + ")", self.width / 4, 4.75 * self.height / 10 - y, 20)
        self.rect(3*self.width/4 - 1.5*self.width/10, 1.30 * self.height/5, 1.5*self.width/5, 2.20*self.height/5, (225, 10, 10))
        self.centered_text("GhostTeam", 3*self.width / 4, 5.5 * self.height / 10, 30)
        self.centered_text(str(gameData["scores"]["ghostteam"]), 3*self.width / 4, 4.75 * self.height / 10, 25)
        y = 0
        for player in gameData["players"]:
            if not gameData["players"][player]["isPacman"]:
                y += 40
                self.centered_text(player + " (" + str(gameData["players"][player]["score"]) + ")", 3*self.width / 4, 4.75 * self.height / 10 - y, 20)

        self.rect(self.width / 4, 0.75 * self.height / 5, self.width / 2, 0.5 * self.height / 5, (80, 80, 255))
        self.centered_text("Suivant", self.width / 2, 1 * self.height / 5, 20)

    def interact_score_screen(self, x, y):
        if self.width/4 < x < 3*self.width/4 and 0.75 * self.height/5 < y < 0.75 * self.height/5 + 0.5*self.height/5:
            return False
        return True

    class Menu():
        """
        fonction qui gère le fonctionnement des menus...

        ...voilà...

        Des questions ?
        """

        def __init__(self, x, y, w, h, title, padding):
            self.position = [x, y]
            self.width = w
            self.height = h
            self.title = title
            self.padding = padding
            self.buttons = []

        def resetAllButtons(self):
            for button in self.buttons:
                button.reset()

        def updateTitle(self, title):
            self.title = title

        def update(self, x, y, w, h, title, padding):
            self.position = [x, y]
            self.width = w
            self.height = h
            self.title = title
            self.padding = padding
            self.updateButtons()

        def draw(self, rect, centered_text, width, height):
            buttonX, buttonY, buttonWidth, buttonHeight = self.computeButtonPos(-1)
            centered_text(self.title, self.position[0]*width + self.width*width / 2, buttonY*height + self.padding*height + buttonHeight*height / 2, 26)
            for button in self.buttons:
                button.draw(rect, centered_text, width, height)

        def checkForClick(self, cursor_pos):
            button_clicked = None
            for button in self.buttons:
                x, y, w, h = button.getData()
                if x < cursor_pos[0] < x + w and y < cursor_pos[1] < y + h:
                    button_clicked = button
            if button_clicked is not None:
                for button in self.buttons:
                    button.reset()
                return button_clicked.click()
            return None

        def addButton(self, label):
            """
            Permet d'ajouter un bouton à un endroit donné.
            """
            x, y, w, h = self.computeButtonPos(len(self.buttons))
            self.buttons.append(self.Button(x, y, w, h, label))
            self.updateButtons()

        def updateButtons(self):
            button_index = 0
            for button in self.buttons:
                x, y, w, h = self.computeButtonPos(button_index)
                button.update(x, y, w, h)
                button_index += 1

        def computeButtonPos(self, buttonIndex):
            buttonsNb = len(self.buttons) + 1
            buttonHeight = (self.height - (self.padding * (buttonsNb + 1))) / buttonsNb
            buttonWidth = self.width - self.padding * 2
            buttonX = self.padding + self.position[0]
            buttonY = self.height - (self.padding + buttonHeight) * (buttonIndex + 2) + self.position[1]
            return buttonX, buttonY, buttonWidth, buttonHeight

        class Button():

            def __init__(self, x, y, w, h, label):
                self.position = [x, y]
                self.width = w
                self.height = h
                self.label = label
                self.clicked = False

            def draw(self, rect, centered_text, width, height):
                """
                Modifie le rendu esthétique d'un bouton lorsqu'il est sélectionné.
                """
                color = (255, 40, 150)
                if self.clicked:
                    color = (40, 255, 140)
                rect(self.position[0]*width, self.position[1]*height, self.width*width, self.height*height, color)
                centered_text(self.label, self.position[0]*width + self.width*width / 2, self.position[1]*height + self.height*height / 2, 24)

            def update(self, x, y, w, h):
                self.__init__(x, y, w, h, self.label)

            def getData(self):
                return self.position[0], self.position[1], self.width, self.height

            def click(self):
                self.clicked = True
                return self.label

            def reset(self):
                self.clicked = False
