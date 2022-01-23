import json
import socket
import selectors
import logging
import types
from typing import List, Dict
from boomcraftApi import BoomcraftApi
from playerRepo import PlayerRepo
from gameEngine import GameEngine
from models.playerInfoModel import PlayerInfoModel
from tool import *
from worker import Worker


class Server:
    def __init__(self, host="0.0.0.0", port=8080):
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.sel = selectors.DefaultSelector()
        self.dico_connect = {}
        self.s_n_connect = {}
        self.boomcraft_api = BoomcraftApi()
        self.player_repo = PlayerRepo()
        self.game_engine = GameEngine(self)

    # region communication
    def __connection(self):
        # AF_INET == ipv4
        # SOCK_STREAM == TCP
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((self.host, self.port))
        lsock.listen()
        self.logger.debug(f"listening on {self.host}:{self.port}")
        lsock.setblocking(False)
        self.sel.register(lsock, selectors.EVENT_READ, data=None)

    def __accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        self.logger.info(f"accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def __service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.outb += recv_data
            else:
                self.logger.info(f'closing connection to{data.addr}', )
                self.sel.unregister(sock)
                sock.close()
            self.__analyse_msg(deserialize(data.outb), key)
            data.outb = b''

    def connect(self):
        self.__connection()
        while True:
            events = self.sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    self.__accept_wrapper(key.fileobj)
                else:
                    self.__service_connection(key, mask)

    def write(self, key, message):
        sock = key.fileobj
        msg_bytes = serialize(message)
        while len(msg_bytes) != 0:
            sent = sock.send(msg_bytes)
            msg_bytes = msg_bytes[sent:]

    def send_all(self, msg):
        for key in self.dico_connect.values():
            self.write(key, msg)

    # endregion

    # region Analyse Message
    def __analyse_msg(self, msg: Dict, key_socket):
        key = first_or_default(msg)
        if key is None:
            return
        body: Dict = msg.get(key, None)
        if msg is None:
            return
        if key == 1:
            mail = body.get("mail")
            password = body.get("password")
            user: PlayerInfoModel = self.__new_player(key_socket, connection_type="login", mail=mail, password=password)
            msg = user.dict()
            msg.pop("key_socket")
            self.write(key_socket, {1: msg})
        elif key == 2:
            body.update({"connection_type": "new"})
            user: PlayerInfoModel = self.__new_player(key_socket, **body)
            msg = user.dict()
            msg.pop("key_socket")
            self.write(key_socket, {1: msg})
        elif key == 3:
            up_player = self.player_repo.update_resources(get_key(self.dico_connect, key_socket), body)
            msg = up_player.dict()
            msg.pop("key_socket")
            self.write(key_socket, {2: msg})
        elif key == 4:
            id_game = self.game_engine.add_player_in_game(self.player_repo.lst_player.get(body.get("id_user")))
            self.write(key_socket, {3: {"id_game": id_game}})
        elif key == 5:
            self.worker = Worker(x=body.get("worker_coord")[0], y=body.get("worker_coord")[0])
        elif key == 6:
            self.worker.destination = [body.get("destination")[0], body.get("destination")[1]]
            self.game_engine.update_road_to_destination(self.worker, key_socket)

        elif key == 100:
            self.s_n_connect.update({body.get("uuid"): key_socket})
        elif key == 101:
            _uuid = body.pop("uuid")
            body.update({"connection_type": "facebook"})
            self.__new_player(self.s_n_connect.get(_uuid), **body)
            # self.write(key_socket, {101: user})
            # self.write(self.dico_connect.get(body.get("id")), {1: user})

    def __new_player(self, key_socket, **data):
        user: PlayerInfoModel = self.player_repo.new_player(key_socket, **data)
        self.dico_connect[user.user.id_user] = key_socket
        return user

    def __add_game(self, id_player):
        return self.game_engine.add_player_in_game(self.player_repo.lst_player.get(id_player))

    # endregion
