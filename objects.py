import pickle
from functools import partial


non_copybacks = [str, int, bool, float, tuple]
important_attributes_c = ["__new__", "__class__", "__init__", "__pizinc_attrs__", "__pizinc_callables__", "__pizinc_name__", "__pizinc_mode__", "__pizinclocal_getattribute__"]
important_attributes_s = ["__new__", "__class__", "__init__", "__pizinc_contained__", "__pizinc_mode__", "__pizinclocal_getattribute__"]

ProxyMode = 1
CopybackMode = 2
LocalMode = 3
ServerMode = 4

DirRequest = 1
WriteRequest = 2
CallRequest = 3
ExecuteRequest = 4
ExecuteClassRequest = 5
DirUpdate = 6


class Container:
    def __init__(self, name=None, connection=None, mode=1, contained=None):
        if connection is not None:
            self.__pizinc_callables__ = connection.send(DirRequest, name)
            self.__pizinc_connection__ = connection
        self.__pizinc_name__ = name
        self.__pizinc_mode__ = mode
        self.__pizinc_contained__ = contained

    def __enter__(self):
        return self.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)

    def __aenter__(self):
        return self.__aenter__()

    def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__aexit__(exc_type, exc_val, exc_tb)

    def __del__(self):
        super().__setattr__("__pizinc_contained__", None)

    def __await__(self):
        return self.__await__()

    def __iter__(self):
        return self.__iter__()

    def __next__(self):
        return self.__next__()

    def __aiter__(self):
        return self.__aiter__()

    def __anext__(self):
        return self.__anext__()

    def __neg__(self):
        return self.__neg__()

    def __oct__(self):
        return self.__oct__()

    def __complex__(self):
        return self.__complex__()

    def __long__(self):
        return self.__long__()

    def __float__(self):
        return self.__float__()

    def __floor__(self):
        return self.__floor__()

    def __ceil__(self):
        return self.__ceil__()

    def __index__(self):
        # TODO: Check that object has an index to prevent a clusterfuck for stuff being used as an index
        return self.__index__()

    def __len__(self):
        return self.__len__()

    def __dir__(self):
        return self.__dir__()

    def __abs__(self):
        return self.__abs__()

    def __bytes__(self):
        return self.__bytes__()

    def __int__(self):
        return self.__int__()

    def __str__(self):
        return self.__str__()

    def __hex__(self):
        return self.__hex__()

    def __floordiv__(self, other):
        return self.__floordiv__(other)

    def __invert__(self):
        return self.__invert__()

    def __bool__(self):
        return self.__bool__()

    def __setitem__(self, key, value):
        return self.__setitem__(key, value)

    def __getitem__(self, item):
        return self.__getitem__(item)

    def __delitem__(self, key):
        return self.__delitem__(key)

    def __setslice__(self, i, j, sequence):
        return self.__setslice__(i, j, sequence)

    def __delslice__(self, i, j):
        return self.__delslice__(i, j)

    def __lshift__(self, other):
        return self.__lshift__(other)

    def __rshift__(self, other):
        return self.__rshift__(other)

    def __add__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self.__sub__(other)

    def __mul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        return self.__div__(other)

    def __truediv__(self, other):
        return self.__truediv__(other)

    def __mod__(self, other):
        return self.__mod__(other)

    def __and__(self, other):
        return self.__and__(other)

    def __or__(self, other):
        return self.__or__(other)

    def __xor__(self, other):
        return self.__xor__(other)

    def __ge__(self, other):
        return self.__ge__(other)

    def __gt__(self, other):
        return self.__gt__(other)

    def __lt__(self, other):
        return self.__lt__(other)

    def __le__(self, other):
        return self.__le__(other)

    def __eq__(self, other):
        return self.__eq__(other)

    def __contains__(self, item):
        return self.__contains__(item)

    def __pow__(self, power, modulo=None):
        return self.__pow__(power, modulo)

    def __getattribute__(self, item):
        """ Use get_attribute of the mode of container """
        mode = super().__getattribute__("__pizinc_mode__")
        if mode == ProxyMode:
            if item in important_attributes_c:
                return super().__getattribute__(item)

            if item not in super().__getattribute__("__pizinc_callables__"):
                data = super().__getattribute__("__pizinc_connection__").send(CallRequest, super().__getattribute__(
                    "__pizinc_name__"), item)
                # IMPLEMENT CALLABLE DETECTION
                if not callable(data):
                    return data

            return partial(super().__getattribute__("__pizinc_connection__").send, CallRequest,
                           super().__getattribute__("__pizinc_name__"), item)
        if mode == LocalMode or mode == ServerMode:
            if item in important_attributes_s:
                return super().__getattribute__(item)
            return getattr(super().__getattribute__("__pizinc_contained__"), item)
        if mode == CopybackMode:
            if item in important_attributes_c:
                return super().__getattribute__(item)

            data = pickle.dumps(super().__getattribute__("__pizinc_contained__"))

            if item not in super().__getattribute__("__pizinc_callables__"):
                data = super().__getattribute__("__pizinc_connection__").send(ExecuteClassRequest, data, item)
                # IMPLEMENT CALLABLE DETECTION
                if not callable(data):
                    return data

            return partial(super().__getattribute__("__pizinc_connection__").send, ExecuteClassRequest,
                           super().__getattribute__("__pizinc_contained__"), item)

