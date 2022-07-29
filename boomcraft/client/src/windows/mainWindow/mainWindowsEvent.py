import time
import pygame

from src.windows.mainWindow.mainWindow import MainWindow


class MainWindowEvent:
    def __init__(self, main_win: MainWindow):
        self.main_win = main_win
        self.__event()

    def __event(self):
        btn = self.main_win.btnAPI
        while True:
            self.main_win.group.update()
            self.main_win.group.draw(self.main_win.gbGame.surface)
            self.main_win.update_gb_banner_resources()
            self.main_win.gbGame.show_groupbox(self.main_win.window)
            self.__handle_input()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn.btn_rect.collidepoint(pygame.mouse.get_pos()):
                        self.main_win.menu_sprite.enlarge()
                        self.main_win.menu_sprite.menu_strip_item.draw(self.main_win.window)
                        self.__menu_strip_on_click()
                    if self.main_win.gbGame.data_rect.collidepoint(pygame.mouse.get_pos()):
                        pos_x = event.pos[0] - self.main_win.gbGame.data_rect.x
                        pos_y = event.pos[1] - self.main_win.gbGame.data_rect.y
                        if pos_x > self.main_win.gbGame.data_rect.width - 17:
                            pos_x = self.main_win.gbGame.data_rect.width - 17
                        if pos_y > self.main_win.gbGame.data_rect.height - 33:
                            pos_y = self.main_win.gbGame.data_rect.height - 33

                        for worker in self.main_win.all_worker.values():
                            if worker.id_owner == self.main_win.user.user.id_user:
                                self.main_win.connection.write({6: {worker.id: (pos_x, pos_y)}})

            pygame.display.update()

    def __menu_strip_on_click(self):
        while True:
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.main_win.menu_sprite.menu_strip_item_dict.get("twitch").rect.collidepoint(
                            pygame.mouse.get_pos()):
                        print("Un")
                    elif self.main_win.menu_sprite.menu_strip_item_dict.get("fcb").rect.collidepoint(
                            pygame.mouse.get_pos()):
                        print("Deux")
                    elif self.main_win.menu_sprite.menu_strip_item_dict.get("discord").rect.collidepoint(
                            pygame.mouse.get_pos()):
                        print("Long")
                    else:
                        self.main_win.menu_sprite.tighten()
                        self.main_win.gbGame.show_groupbox(self.main_win.window)
                        return

    def __handle_input(self):
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_w]:
            print("up")
            time.sleep(0.5)
        if pressed[pygame.K_s]:
            print("down")
        if pressed[pygame.K_a]:
            print("left")
        if pressed[pygame.K_d]:
            print("right")
