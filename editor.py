# editor.py
import display
import objects
import display

class Editor():

    def __init__(self, block_size, origin_x, origin_y, width, height, grid_width, grid_height):
        # Vos initialisations de variables (appelé à l'instanciation de la classe)
        self.block_size = block_size
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.width = width
        self.height = height
        self.screen_width = self.origin_x + self.width
        self.screen_height = self.origin_y + self.height
        self.game = objects.Game(grid_width, grid_height, "level.json")
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.parameters_tool = "Paramètres du niveau"
        self.add_path_tool = "Ajout chemin"
        self.add_gum_tool = "Ajout gum"
        self.add_supergum_tool = "Ajout supergum"
        self.add_pacspawn_tool = "Ajout PacSpawn"
        self.add_ghostspawn_tool = "Ajout GhostSpawn"
        self.remove_tool = "Supprimer"
        self.reset = "Tout effacer"
        self.save_tool = "Sauvegarder"
        self.load_tool = "Charger"
        self.back_to_main_menu = "Retour au menu principal"
        self.tool = self.add_path_tool
        # Menu
        self.menu = display.Draw.Menu(0, 0, self.origin_x/(self.origin_x+self.width), 1, "Edition", 20/(self.origin_y+self.height))
        self.menu.addButton(self.parameters_tool)
        self.menu.addButton(self.add_path_tool)
        self.menu.addButton(self.add_gum_tool)
        self.menu.addButton(self.add_supergum_tool)
        self.menu.addButton(self.add_pacspawn_tool)
        self.menu.addButton(self.add_ghostspawn_tool)
        self.menu.addButton(self.remove_tool)
        self.menu.addButton(self.reset)
        self.menu.addButton(self.save_tool)
        self.menu.addButton(self.load_tool)
        self.menu.addButton(self.back_to_main_menu)


        self.parameters_instance = display.Parameters({"Largeur de la grille": grid_width, "Hauteur de la grille": grid_height})
        self.is_displaying_parameters = False
        self.changed_grid_size = False

        self.click = False
        self.click_pos = [0, 0]

    def on_resize(self, width, height, draw):
        self.screen_width = width
        self.screen_height = height
        origin_x, origin_y, view_width, view_height, block_size = draw.define_viewport(self.grid_width, self.grid_height, True)
        self.block_size = block_size
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.width = view_width
        self.height = view_height
        draw.on_resize(width, height, True, self.game.get_grid_width(), self.game.get_grid_height())
        self.menu.update(0, 0, self.origin_x/(self.origin_x+self.width), 1, "Edition", 20/(self.origin_y+self.height))


    def on_text(self, text, hasToDelete):
        if self.is_displaying_parameters:
            self.parameters_instance.on_text(text, hasToDelete)

    def on_grid_resize(self, draw):
        draw.on_grid_resize(self.grid_width, self.grid_height)
        origin_x, origin_y, view_width, view_height, self.block_size = draw.define_viewport(self.screen_width, self.screen_height, True)
        self.on_resize(self.screen_width, self.screen_height, draw)

    def on_draw(self, draw):
        if self.click:
            self.on_click(self.click_pos[0], self.click_pos[1])
        if self.is_displaying_parameters:
            draw.draw_bckg_rect()
            self.parameters_instance.draw(draw.rect, draw.centered_text, draw.getWidth(), draw.getHeight())
        else:
            if self.changed_grid_size:
                self.changed_grid_size = False
                self.on_grid_resize(draw)
            draw.clear()
            self.game.draw(draw)
            draw.draw_side_rect()
            draw.draw_menu(self.menu)

    def on_click_release(self):
        self.click = False

    def on_click_motion(self, x, y):
        self.click_pos = [x, y]
        if self.click:
            self.on_click(x, y)

    def on_click(self, x, y):
        x2 = x * (self.width + self.origin_x)
        y2 = y*(self.height + self.origin_y)
        if self.is_displaying_parameters and not self.click:
            value = self.parameters_instance.on_click(x, y)
            if value is not None:
                self.is_displaying_parameters = False
                if self.grid_width != int(value["Largeur de la grille"]) or self.grid_height != int(value["Hauteur de la grille"]):
                    self.grid_width = int(value["Largeur de la grille"])
                    self.grid_height = int(value["Hauteur de la grille"])
                    self.game.on_grid_resize(self.grid_width, self.grid_height)
                    self.changed_grid_size = True
        elif self.origin_x < x2 < self.width + self.origin_x and self.origin_y < y2 < self.height + self.origin_y:
            self.click = True
            self.click_pos = [x, y]
            block_x = int((x2 - self.origin_x) / self.block_size)
            block_y = int((y2 - self.origin_y) / self.block_size)
            if self.tool == self.add_path_tool:
                self.add_path(block_x, block_y)
            elif self.tool == self.add_gum_tool:
                self.add_gum(block_x, block_y)
            elif self.tool == self.add_supergum_tool:
                self.add_supergum(block_x, block_y)
            elif self.tool == self.add_pacspawn_tool:
                self.add_pacspawn(block_x, block_y)
            elif self.tool == self.add_ghostspawn_tool:
                self.add_ghostspawn(block_x, block_y)
            elif self.tool == self.remove_tool:
                self.remove(block_x, block_y)
        elif 0 < x < self.origin_x and 0 < y < self.height and not self.click:
            return self.menu_selection(x, y)

    def menu_selection(self, x, y):
        selection = self.menu.checkForClick([x, y])
        if selection != None:
            self.tool = selection
        if selection == self.save_tool:
            self.game.saveGridData()
        if selection == self.load_tool:
            self.game.loadGridData()
            if self.grid_width != self.game.get_grid_width() or self.grid_height != self.game.get_grid_height():
                self.grid_width = self.game.get_grid_width()
                self.grid_height = self.game.get_grid_height()
                self.changed_grid_size = True
        if selection == self.reset:
            self.game.resetGrid()
        if selection == self.parameters_tool:
            self.is_displaying_parameters = True
        if selection == self.back_to_main_menu:
            return True
        return None

    def add_gum(self, x, y):
        self.game.updateBlock(x, y, None, True, None, None, None)

    def add_supergum(self, x, y):
        self.game.updateBlock(x, y, None, None, True, None, None)

    def add_path(self, x, y):
        self.game.updateBlock(x, y, True, None, None, None, None)

    def add_pacspawn(self, x, y):
        self.game.updateBlock(x, y, True, None, None, True, False)

    def add_ghostspawn(self, x, y):
        self.game.updateBlock(x, y, True, None, None, False, True)

    def remove(self, x, y):
        self.game.updateBlock(x, y, False, False, False, False, False)

class MultiplayerEditor():

    def __init__(self, block_size, origin_x, origin_y, width, height, grid_width, grid_height):
        # Vos initialisations de variables (appelé à l'instanciation de la classe)
        self.block_size = block_size
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.width = width
        self.height = height
        self.screen_width = self.origin_x + self.width
        self.screen_height = self.origin_y + self.height
        self.game = objects.Game(grid_width, grid_height, "level_server.json")
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.add_path_tool = "Ajout chemin"
        self.add_gum_tool = "Ajout gum"
        self.add_supergum_tool = "Ajout supergum"
        self.add_pacspawn_tool = "Ajout PacSpawn"
        self.add_ghostspawn_tool = "Ajout GhostSpawn"
        self.remove_tool = "Supprimer"
        self.save_tool = "Sauvegarder"
        self.back_to_main_menu = "Retour au menu principal"
        self.tool = self.add_path_tool
        # Menu
        self.menu = display.Draw.Menu(0, 0, self.origin_x/(self.origin_x+self.width), 1, "Edition", 20/(self.origin_y+self.height))
        self.menu.addButton(self.add_path_tool)
        self.menu.addButton(self.add_gum_tool)
        self.menu.addButton(self.add_supergum_tool)
        self.menu.addButton(self.add_pacspawn_tool)
        self.menu.addButton(self.add_ghostspawn_tool)
        self.menu.addButton(self.remove_tool)
        self.menu.addButton(self.save_tool)
        self.menu.addButton(self.back_to_main_menu)


        self.parameters_instance = display.Parameters({"Largeur de la grille": grid_width, "Hauteur de la grille": grid_height})
        self.is_displaying_parameters = False
        self.changed_grid_size = False

        self.click = False
        self.click_pos = [0, 0]

    def is_grid_loaded(self):
        return self.game.is_loaded_grid()

    def set_grid_data(self, grid_data):
        self.game.setGridData(grid_data)

    def set_grid_changes(self, grid_updates):
        self.game.updateGrid(grid_updates)

    def on_resize(self, width, height, draw):
        self.screen_width = width
        self.screen_height = height
        origin_x, origin_y, view_width, view_height, block_size = draw.define_viewport(self.grid_width, self.grid_height, True)
        self.block_size = block_size
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.width = view_width
        self.height = view_height
        draw.on_resize(width, height, True, self.game.get_grid_width(), self.game.get_grid_height())
        self.menu.update(0, 0, self.origin_x/(self.origin_x+self.width), 1, "Edition", 20/(self.origin_y+self.height))


    def on_text(self, text, hasToDelete):
        if self.is_displaying_parameters:
            self.parameters_instance.on_text(text, hasToDelete)

    def set_grid_size(self, div_x, div_y):
        self.grid_width = div_x
        self.grid_height = div_y

    def on_grid_resize(self, draw):
        draw.on_grid_resize(self.grid_width, self.grid_height)
        origin_x, origin_y, view_width, view_height, self.block_size = draw.define_viewport(self.screen_width, self.screen_height, True)
        self.on_resize(self.screen_width, self.screen_height, draw)

    def on_draw(self, draw):
        if self.click:
            self.on_click(self.click_pos[0], self.click_pos[1])
        if self.is_displaying_parameters:
            draw.draw_bckg_rect()
            self.parameters_instance.draw(draw.rect, draw.centered_text, draw.getWidth(), draw.getHeight())
        else:
            if self.changed_grid_size:
                self.changed_grid_size = False
                self.on_grid_resize(draw)
            draw.clear()
            self.game.draw(draw)
            draw.draw_side_rect()
            draw.draw_menu(self.menu)

    def on_click_release(self):
        self.click = False

    def on_click_motion(self, x, y):
        self.click_pos = [x, y]
        if self.click:
            self.on_click(x, y)

    def on_click(self, x, y):
        x2 = x * (self.width + self.origin_x)
        y2 = y*(self.height + self.origin_y)
        if self.is_displaying_parameters and not self.click:
            value = self.parameters_instance.on_click(x, y)
            if value is not None:
                self.is_displaying_parameters = False
                if self.grid_width != int(value["Largeur de la grille"]) or self.grid_height != int(value["Hauteur de la grille"]):
                    self.grid_width = int(value["Largeur de la grille"])
                    self.grid_height = int(value["Hauteur de la grille"])
                    self.game.on_grid_resize(self.grid_width, self.grid_height)
                    self.changed_grid_size = True
        elif self.origin_x < x2 < self.width + self.origin_x and self.origin_y < y2 < self.height + self.origin_y:
            self.click = True
            self.click_pos = [x, y]
            block_x = int((x2 - self.origin_x) / self.block_size)
            block_y = int((y2 - self.origin_y) / self.block_size)
            if self.tool == self.add_path_tool:
                return self.add_path(block_x, block_y)
            elif self.tool == self.add_gum_tool:
                return self.add_gum(block_x, block_y)
            elif self.tool == self.add_supergum_tool:
                return self.add_supergum(block_x, block_y)
            elif self.tool == self.add_pacspawn_tool:
                return self.add_pacspawn(block_x, block_y)
            elif self.tool == self.add_ghostspawn_tool:
                return self.add_ghostspawn(block_x, block_y)
            elif self.tool == self.remove_tool:
                return self.remove(block_x, block_y)
        elif 0 < x < self.origin_x and 0 < y < self.height and not self.click:
            return self.menu_selection(x, y)

    def menu_selection(self, x, y):
        selection = self.menu.checkForClick([x, y])
        if selection != None:
            self.tool = selection
        if selection == self.save_tool:
            self.game.saveGridData()
        if selection == self.back_to_main_menu:
            return True
        return None

    def add_gum(self, x, y):
        return self.game.createChange(x, y, None, True, None, None, None)

    def add_supergum(self, x, y):
        return self.game.createChange(x, y, None, None, True, None, None)

    def add_path(self, x, y):
        return self.game.createChange(x, y, True, None, None, None, None)

    def add_pacspawn(self, x, y):
        return self.game.createChange(x, y, True, None, None, True, False)

    def add_ghostspawn(self, x, y):
        return self.game.createChange(x, y, True, None, None, False, True)

    def remove(self, x, y):
        return self.game.createChange(x, y, False, False, False, False, False)