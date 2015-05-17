import logging
import tornado.httpserver
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
from tornado.options import define, options

from collections import defaultdict

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/', LogIn),
            (r'/room/(?P<room>.*)?', Room),
            (r'/chatws/(?P<room>.*)?', ChatWS),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            debug=True
        )
        super(Application, self).__init__(handlers, **settings)


class LogIn(tornado.web.RequestHandler):

    def get(self):
        self.render("login.html")

    def post(self):
        self.set_header("Content-Type", "text/plain")
        user = self.get_body_argument("user")
        room = self.get_body_argument("room")
        self.set_secure_cookie('user', user)
        self.set_secure_cookie('room', room)
        self.redirect('/room/{}'.format(room))


class Room(tornado.web.RequestHandler):

    def get(self, **route_params):
        self.render("room.html")

class ChatWS(tornado.websocket.WebSocketHandler):
    #TODO: implennet new rooms dict structure
    #rooms is a dict with key the room name and value a set of tuples (user, wsHandler)
    # {'room': set(('user1': wsHandler1), ('user2': wsHandler2))

    rooms = defaultdict(set)

    def open(self, room):
        print("Dan Socket Opened")
        ChatWS.rooms[room].add((self.get_secure_cookie('user'), self))
        print(ChatWS.rooms)


    def on_close(self):
        ChatWS.rooms[self.path_kwargs['room']].remove((self.get_secure_cookie('user'), self))
        print("Dan Socket Closed")


    def on_message(self, msg):
        parsed = tornado.escape.json_decode(msg)
        print(parsed)
        ChatWS.send_updates(parsed)

    @classmethod
    def send_updates(cls, msg):
        for user, ws_handler in cls.rooms[msg['room']]:
            try:
                print(ws_handler)
                ws_handler.write_message(msg)
            except:
                logging.error("Error sending message", exc_info=True)


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
