import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
from tornado.options import define, options

from collections import defaultdict


define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', Dan),
            (r'/room/(?P<room>.*)?', Dan),
            (r'/chatws/(?P<room>.*)?', DanSocket)
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True
        )
        tornado.web.Application.__init__(self, handlers, debug=True, **settings)


class Dan(tornado.web.RequestHandler):
    def get(self, **route_params):
        self.render("index.html")

class DanSocket(tornado.websocket.WebSocketHandler):
    #rooms is a dict with key the room name and value a set of webSockethandlers
    rooms = defaultdict(set)

    def open(self, room):
        print("Dan Socket Opened")
        DanSocket.rooms[room].add(self)
        

    def on_close(self):
        DanSocket.rooms[self.path_kwargs['room']].remove(self)
        print("Dan Socket Closed")

    def on_message(self, msg):
        parsed = tornado.escape.json_decode(msg)
        print(parsed)
        DanSocket.send_updates(parsed)

    @classmethod
    def send_updates(cls, msg):
        for web_socket in cls.rooms[msg['room']]:
            try:
                print(web_socket)
                web_socket.write_message(msg)
            except:
                logging.error("Error sending message", exc_info=True)


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
