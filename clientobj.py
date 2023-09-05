from functools import partial

operators = {"__iadd__": "__add__",
             "__isub__": "__sub__",
             "__imul__": "__mul__",
             "__imatmul__": "__matmul__",
             "__itruediv__": "__truediv__",
             "__ifloordiv__": "__floordiv__",
             "__imod__": "__mod__",
             "__ipow__": "__pow__",
             "__ilshift__": "__lshift__",
             "__irshift__": "__rshift__",
             "__iand__": "__and__",
             "__ixor__": "__xor__",
             "__ior__": "__or__",}


def read(attr, *args):
    print("BING BONG")


def patch_getattribute(cls):
    __class__ = cls

    def getattribute(self, attr):
        print(attr)
        if attr in dir(type(self)) and attr in super().__getattribute__("__pizic_callable__"):
            return super().__getattribute__(attr)
        # TODO: implement copy-over
        return read(attr)
    
    cls.__getattribute__ = getattribute


def new_class(name, attrs, callable_attrs):
    # Generate list of augmented operators as they will not work ordinarily through the clientside class
    operators_filtered = [augment for augment in operators.keys() 
                          if operators[augment] in attrs
                          and not augment in attrs]
    attrs.extend(operators_filtered)

    # Create attributes dictionary and filter out ones that may break operation
    calls = {attr: partial(read, attr) for attr in attrs}
    calls["__pizic_callable__"] = callable_attrs
    del calls["__new__"]
    del calls["__class__"]
    del calls["__init__"]
    
    # Patch get attribute to support classes using getattr
    cls = type(name, (), calls)
    patch_getattribute(cls)
    return cls


callables = [attr for attr in dir(int) if callable(getattr(int, attr))]

integer = new_class("Integer", callables, dir(int))

x = integer()
print(dir(integer))
