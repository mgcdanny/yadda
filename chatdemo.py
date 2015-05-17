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
    #rooms is a dict with key the room name and value a set of tuples (user, wsHandler)
    # {'room': {'user1': wsHandler1, 'user2':wsHandler2}}

    rooms = defaultdict(dict)

    def open(self, room):
        print("Chat Socket Opened")
        ChatWS.rooms[room][self.get_secure_cookie('user')] = self
        print(ChatWS.rooms)

    def on_close(self):
        del ChatWS.rooms[self.path_kwargs['room']][self.get_secure_cookie('user')]
        print("Chat Socket Closed")

    def on_message(self, msg):
        parsed = tornado.escape.json_decode(msg)
        parsed['user'] = self.get_secure_cookie('user').decode("utf-8")
        ChatWS.send_updates(parsed)

    @classmethod
    def send_updates(cls, msg):
        for user, ws_handler in cls.rooms[msg['room']].items():
            try:
                msg['buddies'] = [buddy.decode("utf-8") for buddy in cls.rooms[msg['room']].keys()]
                ws_handler.write_message(msg)
            except:
                logging.error("Error sending message", exc_info=True)

    @classmethod
    def update_buddies_list(self, room):            
        buddies = []
        for user, ws_handler in cls.rooms[msg['room']]:
            buddies.append(user)
        return buddies



def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
