import conn
from objects import Container, ProxyMode, ServerMode, DirUpdate


class __Failed:
    pass


OperationFailed = __Failed()


class Pizinc(conn.PizincConnection):
    def __init__(self, port, host="127.0.0.1"):
        super().__init__(port, host=host)

    def share(self, obj, name):
        obj = Container(contained=obj, mode=ServerMode)
        self.objects[name] = obj

        if self.connected():
            callables = [attr for attr in dir(obj) if callable(getattr(obj, attr))]
            self.conn.send(DirUpdate, name, callables)
        return obj

    def sync(self, name):
        return Container(name=name, connection=self, mode=ProxyMode)

    def connected(self):
        return self.conn is not None and self.running
