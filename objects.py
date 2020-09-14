#objects.py
import json
import copy

class Block():

    def __init__(self, isPath, hasGum, isSuperGum, isPacmanSpawn, isGhostSpawn):
        self.hasGum = hasGum
        self.isPath = isPath
        self.isSuperGum = isSuperGum
        self.isPacmanSpawn = isPacmanSpawn
        self.isGhostSpawn = isGhostSpawn

    def setGum(self, value):
        self.hasGum = value

    def setPath(self, value):
        self.isPath = value

    def setSuperGum(self, value):
        self.isSuperGum = value

    def setPacmanSpawn(self, value):
        self.isPacmanSpawn = value

    def setGhostSpawn(self, value):
        self.isGhostSpawn = value

    def getGum(self):
        return self.hasGum

    def getPath(self):
        return self.isPath

    def getSuperGum(self):
        return self.isSuperGum

    def getPacmanSpawn(self):
        return self.isPacmanSpawn

    def getGhostSpawn(self):
        return self.isGhostSpawn

    def getData(self):
        return {"hasGum": self.hasGum, "isPath": self.isPath, "isSuperGum": self.isSuperGum, "isPacmanSpawn": self.isPacmanSpawn, "isGhostSpawn": self.isGhostSpawn}

    def draw(self, draw, x, y, block_size, layer):
        if self.isPath and layer == 0:
            draw.rect_in_viewport(x * block_size - block_size / 10, y * block_size - block_size / 10,
                                  block_size + 2 * block_size / 10,
                                  block_size + 2 * block_size / 10, (80, 80, 255))
        if self.isGhostSpawn and layer == 1:
            draw.rect_in_viewport(x * block_size, y * block_size, block_size, block_size, (80, 20, 20))
        elif self.isPacmanSpawn and layer == 1:
            draw.rect_in_viewport(x * block_size, y * block_size, block_size, block_size, (20, 80, 80))
        elif self.isPath and layer == 1:
            draw.rect_in_viewport(x * block_size, y * block_size, block_size, block_size, (20, 20, 20))
        if self.isPath and self.hasGum and layer == 2 and not self.isSuperGum:
            draw.rect_in_viewport(x * block_size + 2 * block_size / 5, y * block_size + 2 * block_size / 5,
                                  block_size / 5, block_size / 5,
                                  (255, 255, 255))
        if self.isPath and self.hasGum and layer == 2 and self.isSuperGum:
            draw.rect_in_viewport(x * block_size + 3 * block_size / 10, y * block_size + 3 * block_size / 10,
                                  4 * block_size / 10,
                                  4 * block_size / 10,
                                  (255, 255, 255))


class Game():

    def __init__(self, grid_width, grid_height, grid_file):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.grid_file = grid_file
        self.loaded_grid = False
        self.global_changes = []
        self.grid = self.gridGenerator1()

    def get_grid_width(self):
        return self.grid_width

    def get_grid_height(self):
        return self.grid_height

    def on_grid_resize(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.resetGrid()

    def resetGrid(self):
        self.grid = self.gridGenerator1()

    def reverseChanges(self):
        for changes in self.global_changes:
            for change in changes:
                if change["isPath"] is True:
                    change["isPath"] = False
                elif change["isPath"] is False:
                    change["isPath"] = True


                if change["hasGum"] is True:
                    change["hasGum"] = False
                elif change["hasGum"] is False:
                    change["hasGum"] = True


                if change["isSuperGum"] is True:
                    change["isSuperGum"] = False
                elif change["isSuperGum"] is False:
                    change["isSuperGum"] = True

                if change["isPacmanSpawn"] is True:
                    change["isPacmanSpawn"] = False
                elif change["isPacmanSpawn"] is False:
                    change["isPacmanSpawn"] = True

                if change["isGhostSpawn"] is True:
                    change["isGhostSpawn"] = False
                elif change["isGhostSpawn"] is False:
                    change["isGhostSpawn"] = True

        safeChanges = copy.deepcopy(self.global_changes)

        for changes in safeChanges:
            self.setGridChanges(changes)

        self.global_changes.clear()

    def getSpawnBlocks(self, isPacman):
        blockList = []
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[x][y].getPacmanSpawn() and isPacman:
                    blockList.append((x, y))
                elif self.grid[x][y].getGhostSpawn() and not isPacman:
                    blockList.append((x, y))
        return blockList

    def countGum(self):
        gumCount = 0
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[x][y].getGum() and self.grid[x][y].getPath():
                    gumCount += 1
        return gumCount

    def updateGrid(self, gridUpdates):
        for gridChanges in gridUpdates:
            self.setGridChanges(gridChanges)

    def setGridChanges(self, changes):
        for change in changes:
            self.updateBlock(change["x"], change["y"], change["isPath"], change["hasGum"], change["isSuperGum"], change["isPacmanSpawn"], change["isGhostSpawn"])
        self.global_changes.append(changes)


    def is_loaded_grid(self):
        return self.loaded_grid

    def gridGenerator1(self):
        grid = []
        for y in range(self.grid_width):
            xLine = []
            for x in range(self.grid_height):
                xLine.append(Block(False, False, False, False, False))
            grid.append(xLine)
        self.global_changes.clear()
        return grid

    def getGridData(self):
        gridData = {"dimensions": [self.grid_width, self.grid_height], "grid": []}
        grid = []
        for xLine in self.grid:
            gridXLine = []
            for block in xLine:
                gridXLine.append(block.getData())
            grid.append(gridXLine)
        gridData["grid"] = grid
        return gridData

    def setGridData(self, new_data):
        self.grid_width = new_data["dimensions"][0]
        self.grid_height = new_data["dimensions"][1]
        grid = new_data["grid"]
        grid_objects = []
        for x in range(self.grid_width):
            xLine = []
            for y in range(self.grid_height):
                 xLine.append(Block(grid[x][y]["isPath"],
                              grid[x][y]["hasGum"],
                              grid[x][y]["isSuperGum"],
                              grid[x][y]["isPacmanSpawn"],
                              grid[x][y]["isGhostSpawn"]))
            grid_objects.append(xLine)
        self.grid = grid_objects

        self.global_changes.clear()
        self.loaded_grid = True

    def saveGridData(self):
        with open(self.grid_file, "w") as text_file:
            text_file.write(json.dumps(self.getGridData()))


    def loadGridData(self):
        with open(self.grid_file, "r") as text_file:
            data = json.loads(text_file.read())
            self.setGridData(data)

    def setPath(self, x, y, value):
        self.grid[x][y].setPath(value)

    def createChange(self, x, y, isPath, hasGum, isSuperGum, isPacmanSpawn, isGhostSpawn):
        return {"x": x, "y": y, "hasGum": hasGum, "isPath": isPath, "isSuperGum": isSuperGum, "isPacmanSpawn": isPacmanSpawn, "isGhostSpawn": isGhostSpawn}

    def updateBlock(self, x, y, isPath, hasGum, isSuperGum, isPacmanSpawn, isGhostSpawn):
        if isPath != None:
            self.grid[x][y].setPath(isPath)
        if hasGum != None:
            self.grid[x][y].setGum(hasGum)
        if isSuperGum != None:
            self.grid[x][y].setSuperGum(isSuperGum)
        if isPacmanSpawn != None:
            self.grid[x][y].setPacmanSpawn(isPacmanSpawn)
        if isGhostSpawn != None:
            self.grid[x][y].setGhostSpawn(isGhostSpawn)
        return {"x": x, "y": y, "hasGum": hasGum, "isPath": isPath, "isSuperGum": isSuperGum, "isPacmanSpawn": isPacmanSpawn, "isGhostSpawn": isGhostSpawn}

    def getBlock(self, x, y):
        if 0 <= x < len(self.grid) and 0 <= y < len(self.grid[x]):
            return self.grid[x][y].getData()
        return None

    def draw(self, draw):
        for layer in range(3):
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    self.grid[x][y].draw(draw, x, y, draw.get_block_size(), layer)
