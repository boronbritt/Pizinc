import threading
import socket
import struct
import random
import weakref
import select
import sys
import pickle
import objects
import dill
from collections.abc import Iterable

DirRequest = 1
WriteRequest = 2
CallRequest = 3
ExecuteRequest = 4
ExecuteClassRequest = 5
DirUpdate = 5


def try_pull(obj):
    if type(obj) == objects.Container:
        return obj.__pizinc_contained__
    return obj


class TagProtocol:
    def __init__(self, port, host="127.0.0.1"):
        weakref.finalize(self, setattr, self, "running", False)
        self.host = host
        self.port = port
        self.conn = None
        self.lock = threading.Lock()
        self.response_events = {}
        self.response_data = {}
        self.timeout = 0.05
        self.running = True
        self.listen_thread = threading.Thread(target=self.start, daemon=True)
        self.listen_thread.start()

    def alive(self):
        if self.running and sys.getrefcount(self) > 6: return True
        return False

    def close(self):
        self.conn = None
        self.running = False

    def recv(self, length):
        data = b''
        while len(data) < length:
            ready = select.select([self.conn], [], [], self.timeout)
            if not self.alive():
                self.conn.close()
                self.close()
                sys.exit()
            if ready[0]:
                data += self.conn.recv(length - len(data))
        return data

    def register_response_handler(self, tag):
        """Registers a callback function to handle incoming responses with the specified tag"""
        event = threading.Event()
        self.response_events[tag] = event

    def handle_request(self, tag, data):
        """This should be overridden by a subclass to handle incoming requests
        :rtype: object
        """
        pass

    def start(self):
        if self.conn is not None:
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, self.port))
                s.listen()
                s.setblocking(False)
                while self.conn is None:
                    ready = select.select([s], [], [], self.timeout)
                    if not self.alive():
                        s.close()
                        return
                    if ready[0]:
                        self.conn, addr = s.accept()
                self.listen()
        except OSError as e:
            if e.errno == 98:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.port))
                    s.setblocking(False)
                    self.conn = s
                    self.listen()

    def listen(self):
        """Listens for incoming data and calls the appropriate callback function"""
        while self.running:
            data = self.recv(16)
            if not data:
                break
            tag, length = struct.unpack('>QQ', data)
            data = self.recv(length)
            if tag in self.response_events:
                event = self.response_events[tag]
                self.response_data[tag] = data
                event.set()
            else:
                self.handle_request(tag, data)

    def send_request(self, tag, data):
        """Sends a request with the specified tag and data, and waits for a response with the specified response tag"""
        self.register_response_handler(tag)

        if self.conn is None:
            return None
        with self.lock:
            message = struct.pack('>QQ', tag, len(data)) + data
            self.conn.sendall(message)
            event = self.response_events[tag]
            event.wait()
            return self.response_data[tag]

    def send_response(self, tag, data):
        """Sends a response with the specified tag and data"""

        if self.conn is None:
            return
        with self.lock:
            message = struct.pack('>QQ', tag, len(data)) + data
            self.conn.sendall(message)


class PizincConnection(TagProtocol):
    def __init__(self, port, host="127.0.0.1"):
        super().__init__(port, host=host)
        self.objects = weakref.WeakValueDictionary()

    def send_serialized(self, *args):
        request_tag = random.getrandbits(64)
        request_data = pickle.dumps(args)
        response = self.send_request(request_tag, request_data)

        return pickle.loads(response)

    def handle_request(self, tag, data):
        response_data = None
        data = pickle.loads(data)

        code = data[0]

        if code == 1:
            response_data = self.handle_dir_request(data[1])
        elif code == 2:
            response_data = self.handle_write_request(data[1], data[2])
        elif code == 3:
            # TODO : CALLBACK
            response_data = self.handle_call_request(data[1], data[2], data[3:])
        elif code == 4:
            response_data = self.handle_execute_call_request(data[1], data[2], data[3:])
        elif code == 6:
            response_data = self.handle_dir_update(data[1], data[2])

        self.send_response(tag, pickle.dumps(response_data))

    def handle_dir_request(self, object_name):
        try:
            obj = self.objects[object_name].__pizinc_contained__

            attrs = dir(obj)
            callables = [attr for attr in attrs if callable(getattr(obj, attr))]
            return True, callables
        except KeyError:
            return False, None

    def handle_write_request(self, object_name, data):
        try:
            obj = self.objects[object_name]
            obj.__pizinc_contained__ = data

            attrs = dir(obj.__pizinc_contained__)
            callables = [attr for attr in attrs if callable(getattr(obj.__pizinc_contained__, attr))]
            return True, callables
        except KeyError:
            return False, None

    def handle_call_request(self, object_name, attr, args):
        success, data = False, None
        try:
            obj = getattr(self.objects[object_name], attr)
            if args is not None and callable(obj):
                if isinstance(args, Iterable):
                    obj = obj(*args)
                else:
                    obj = obj(args)
            # TODO: Handle increment overloads
            success, data = True, obj
        except Exception as e:
            print(e)
        finally:
            return success, data

    def handle_dir_update(self, object_name, callables):
        success, data = False, None
        try:
            if object_name in self.objects:
                obj = self.objects[object_name]
                setattr(obj, "__pizinc_callables__", callables)
                success, data = True, True
        finally:
            return success, data

    @staticmethod
    def handle_execute_request(function, args):
        success = False
        data = None
        try:
            data = function(*args)
            success = True
        finally:
            return success, data

    @staticmethod
    def handle_execute_call_request(cls, function, args):
        success = False
        data = None
        try:
            attr = getattr(cls, function)
            if args is not None:
                args = [try_pull(arg) for arg in args]
                attr = attr(*args)
            success, data = True, attr
        finally:
            return success, data

    def send(self, *args):
        success, data = self.send_serialized(*args)
        if not success:
            return None

        if type(data) not in objects.non_copybacks:
            data = objects.Container(contained=data, mode=objects.CopybackMode)

        return data
