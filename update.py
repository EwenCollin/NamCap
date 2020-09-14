# update.py
import time
import socket
import threading
import json

import objects
import random
import math


server = None


def playerDefeat(players):
    for player in players:
        for player2 in players:
            if player != player2:
                if computeDistanceFromPositions(players[player]["position"], players[player2]["position"]) < 1:
                    if players[player]["isPacman"] and players[player]["isSuper"] and not players[player2]["isPacman"] and not players[player2]["isEscaping"]:
                        players[player]["hasEaten"] = True
                        players[player2]["isEscaping"] = True
                    elif players[player]["isPacman"] and not players[player]["isSuper"] and not players[player2]["isPacman"] and not players[player2]["isEscaping"]:
                        players[player]["respawn"] = True
                        players[player2]["hasEaten"] = True
    return players

def computeDistanceFromPositions(position1, position2):
    return math.sqrt(math.pow(position1[0] - position2[0], 2) + math.pow(position1[1] - position2[1], 2))

class Updater():

    def __init__(self, id, dt, dt_input):
        self.id = id
        self.dt = dt
        self.dt_input = dt_input
        self.speed_multiplier = 10
        self.speed = [0.0, 0.0]
        self.time_speed = self.dt*self.speed_multiplier
        self.player_width = 1.0
        self.player_height = 1.0
        self.idle_move = True
        self.last_user_inputs = [0, 0]
        self.position = [0.0, 0.0]
        self.div_x = 0
        self.div_y = 0
        self.gridData = {}
        self.player = {}

    def run(self, player, server_instance):
        """
        lit les imputs du client, execute compute_pos et met à jour ses coordonnées
        """
        global server
        server = server_instance
        self.player = player
        self.speed = player["speed"]
        self.last_user_inputs = self.update_speed(player["inputs"])
        self.idle_move = player["idleMove"]
        self.position = player["position"]
        self.gridData = server_instance.getGridData()
        self.div_x = self.gridData["dimensions"][0]
        self.div_y = self.gridData["dimensions"][1]


        #General game logic relative to player



        if self.player["respawn"]:
            self.spawn()
            player["respawn"] = False
            self.idle_move = True
            self.speed = [0, 0]
        if self.player["isEscaping"]:
            self.speed_multiplier = self.speed_multiplier*1.5
            self.time_speed = self.dt*self.speed_multiplier
            block = server.getBlock(round(self.position[0] + self.player_width / 2),
                                    round(self.position[1] + self.player_height / 2))
            if block is not None and "isGhostSpawn" in block and block["isGhostSpawn"]:
                player["isEscaping"] = False
        if self.player["hasEaten"]:
            player["score"] += 10
            player["hasEaten"] = False
        if self.player["coolDown"] > 0:
            self.player["coolDown"] -= 1
        else:
            self.player["isSuper"] = False


        if self.gridData["dimensions"][1] > self.gridData["dimensions"][0]:
            self.time_speed = self.time_speed*28/self.gridData["dimensions"][1]
        else:
            self.time_speed = self.time_speed*28/self.gridData["dimensions"][0]

        player["position"] = self.compute_pos(player["inputs"])
        player["speed"] = self.speed
        player["idleMove"] = self.idle_move
        player["isSuper"] = self.player["isSuper"]
        player["coolDown"] = self.player["coolDown"]
        gridChange = self.removeGum()
        #print(player)
        return player, gridChange

    def spawn(self):
        spawnBlocks = server.getSpawnBlocks(self.player["isPacman"])
        spawn_block_index = random.randint(0, len(spawnBlocks) - 1)
        self.position = [spawnBlocks[spawn_block_index][0], spawnBlocks[spawn_block_index][1]]

    def removeGum(self):
        block = server.getBlock(round(self.position[0]), round(self.position[1]))
        if self.player["isPacman"] \
                and block is not None and block["hasGum"]:
            if block["isSuperGum"]:
                self.player["isSuper"] = True
                self.player["coolDown"] = 300
            return server.updateBlock(round(self.position[0]), round(self.position[1]), None, False, None, None, None)
        return None

    def speed_timed(self, L):
        """
        convertit les inputs en vitesse
        """
        new_speed = [L[0] * self.time_speed, L[1] * self.time_speed]
        return new_speed

    def position_timed(self):
        """
        convertit la vitesse en position
        temps_position = actual_time - self.last_time_position
        """
        actual_time = time.time()
        self.position[0] = self.speed[0] * self.time_speed + self.position[0]
        self.position[1] = self.speed[1] * self.time_speed + self.position[1]
        self.last_time_position = actual_time
        return self.position

    def update_speed(self, input):
        L = [0, 0]
        if input[0] > 0:
            L[0] = 1
        elif input[0] < 0:
            L[0] = -1
        if input[1] > 0:
            L[1] = 1
        elif input[1] < 0:
            L[1] = -1
        return L

    def compute_pos(self, L):
        """
        calcule la position d'un joueur à l'étape n+1
        prend en compte tor_pos

        entrée: L = imput directionnel du joueur

        sortie: retourne la position du joueur
        """
        if not self.is_move_valid(self.speed_timed(self.speed)) or (
                self.is_move_valid(self.speed_timed(self.speed_timed(L))) and \
                ((L[0] > 0 > self.speed[0]) or (L[0] < 0 < self.speed[0]) or (L[1] < 0 < self.speed[1]) or (
                        L[1] > 0 > self.speed[1]) or (L[0] != 0 and self.speed[1] != 0) or (
                         L[1] != 0 and self.speed[0] != 0))) \
                or self.idle_move:
            self.time_speed = self.dt_input*self.speed_multiplier
            new_speed = self.speed_timed(L)
        else:
            if self.dt != self.dt_input:
                new_speed = self.speed
            else:
                new_speed = self.speed_timed(self.update_speed(self.speed))
        if self.is_move_valid(self.speed_timed(new_speed)):
            self.idle_move = False
            self.speed = new_speed
            self.position_timed()
            self.tor_pos()
        else:
            self.idle_move = True
            self.position[0] = round(self.position[0])
            self.position[1] = round(self.position[1])
        return self.position

    def tor_pos(self):
        """
        Permet, quand le joueur atteint un bord de l'écran, de se retrouver de l'autre coté.
        """
        if self.position[0] + self.player_width / 2 > self.div_x:
            self.position[0] = - self.player_width / 2
        elif self.position[0] + self.player_width / 2 < 0:
            self.position[0] = self.div_x - self.player_width / 2
        if self.position[1] + self.player_height / 2 < 0:
            self.position[1] = self.div_y - self.player_height / 2
        elif self.position[1] + self.player_height / 2 > self.div_y:
            self.position[1] = - self.player_height / 2

    def is_move_valid(self, speed):
        """
        Vérifie par le calcul si le block à position + vitesse du joueur correspondra à un chemin.
        """
        block = server.getBlock(round(self.position[0] + speed[0] + self.player_width / 2),
                                round(self.position[1] + speed[1]))
        if speed[0] > 0 and block is not None and "isPath" in block and block["isPath"] and \
                -self.time_speed * self.time_speed < self.position[1] + speed[1] - round(
            self.position[1] + speed[1]) < self.time_speed * self.time_speed:
            if (block["isPacmanSpawn"] and self.player["isPacman"]) or (block["isGhostSpawn"] \
                and not self.player["isPacman"]) or (not block["isPacmanSpawn"] and not block["isGhostSpawn"]):
                return True
        elif speed[0] > 0 and block is None and \
                -self.time_speed * self.time_speed < self.position[1] + speed[1] - round(
            self.position[1] + speed[1]) < self.time_speed * self.time_speed:
            return True

        block = server.getBlock(round(self.position[0] + speed[0] - self.player_width / 2),
                                round(self.position[1] + speed[1]))
        block2 = server.getBlock(round(self.position[0] + speed[0] + self.player_width / 2),
                                 round(self.position[1] + speed[1]))
        if speed[0] < 0 and block is not None and "isPath" in block and block["isPath"] and \
                -self.time_speed * self.time_speed < self.position[1] + speed[1] - round(
            self.position[1] + speed[1]) < self.time_speed * self.time_speed:
            if (block["isPacmanSpawn"] and self.player["isPacman"]) or (block["isGhostSpawn"] \
                and not self.player["isPacman"]) or (not block["isPacmanSpawn"] and not block["isGhostSpawn"]):
                return True
        elif speed[0] < 0 and block is None and block2 is not None and "isPath" in block2 and block2["isPath"] and \
                -self.time_speed * self.time_speed < self.position[1] + speed[1] - round(
            self.position[1] + speed[1]) < self.time_speed * self.time_speed:
            if (block2["isPacmanSpawn"] and self.player["isPacman"]) or (block2["isGhostSpawn"] \
                and not self.player["isPacman"]) or (not block2["isPacmanSpawn"] and not block2["isGhostSpawn"]):
                return True

        block = server.getBlock(round(self.position[0] + speed[0]),
                                round(self.position[1] + speed[1] + self.player_height / 2))
        if speed[1] > 0 and block is not None and "isPath" in block and block["isPath"] and \
                - self.time_speed * self.time_speed < self.position[0] + speed[0] - round(
            self.position[0] + speed[0]) < self.time_speed * self.time_speed:
            if (block["isPacmanSpawn"] and self.player["isPacman"]) or (block["isGhostSpawn"] \
                and not self.player["isPacman"]) or (not block["isPacmanSpawn"] and not block["isGhostSpawn"]):
                return True
        elif speed[1] > 0 and block is None and \
                - self.time_speed * self.time_speed < self.position[0] + speed[0] - round(
            self.position[0] + speed[0]) < self.time_speed * self.time_speed:
            return True

        block = server.getBlock(round(self.position[0] + speed[0]),
                                round(self.position[1] + speed[1] - self.player_height / 2))
        block2 = server.getBlock(round(self.position[0] + speed[0]),
                                 round(self.position[1] + speed[1] + self.player_height / 2))
        if speed[1] < 0 and block is not None and "isPath" in block and block["isPath"] and \
                - self.time_speed * self.time_speed < self.position[0] + speed[0] - round(
            self.position[0] + speed[0]) < self.time_speed * self.time_speed:
            if (block["isPacmanSpawn"] and self.player["isPacman"]) or (block["isGhostSpawn"] \
                and not self.player["isPacman"]) or (not block["isPacmanSpawn"] and not block["isGhostSpawn"]):
                return True
        elif speed[1] < 0 and block is None and block2 is not None and "isPath" in block2 and block2["isPath"] and \
                - self.time_speed * self.time_speed < self.position[0] + speed[0] - round(
            self.position[0] + speed[0]) < self.time_speed * self.time_speed:
            if (block2["isPacmanSpawn"] and self.player["isPacman"]) or (block2["isGhostSpawn"] \
                and not self.player["isPacman"]) or (not block2["isPacmanSpawn"] and not block2["isGhostSpawn"]):
                return True

        return False