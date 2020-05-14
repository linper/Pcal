import math
import sys
import re
import function as f
from os import system
import pickle

param_pattern = re.compile(r"p[\d]+")
number_pattern = re.compile(r"(^(0[bB])[01]+$)|(^(0[oO])[0-7]+$)|(^(0[xX])[0-9a-fA-F]+$)|(^[-+]?[0-9]*$)|(^[-+]?"
                            r"[0-9]*\.[0-9]+$)|(^[-+]?[0-9]*\.?[0-9]+e[-+]?[0-9]+$)")
exec_pattern = re.compile(r"^([\w\d_]+(\([\w\d\s_]+\)))+|([\w\d()+*\-/.,^=%!|&\"_]+)\s*$")
name_pattern = re.compile(r"^[a-zA-Z_][\w_]*")

u_funs = {}
vars = {}


# functions
def sum(*args):
    s = 0.0
    for i in range(len(args)):
        s += args[i]
    return s


def sub(*args):
    s = float(args[0])
    for i in range(1, len(args)):
        s -= args[i]
    return s


def div(*args):
    s = float(args[0])
    for i in range(1, len(args)):
        s /= args[i]
    return s


def mul(*args):
    s = 1.0
    for i in range(len(args)):
        s *= args[i]
    return s


def pow(*args):
    s = float(args[0])
    for i in range(1, len(args)):
        s **= args[i]
    return s


def abs(*args):
    return math.fabs(args[0])


def tan(*args):
    return math.tan(args[0])


def atan(*args):
    return math.atan(args[0])


def sin(*args):
    return math.sin(args[0])


def asin(*args):
    return asin(args[0])


def cos(*args):
    return math.cos(args[0])


def acos(*args):
    return math.acos(args[0])


def forwad(*args):
    return args[0]


funs = {"+": (sum, 256), "-": (sub, 256), "/": (div, 256), "*": (mul, 256), "**": (pow, 32),
        "sum": (sum, 256), "sub": (sub, 256), "div": (div, 256), "mul": (mul, 256), "pow": (pow, 32), "abs": (abs, 1),
        "tan": (tan, 1), "atan": (atan, 1), "sin": (sin, 1), "asin": (asin, 1), "cos": (cos, 1), "acos": (acos, 1),
        "forward": (forwad, 1)}

# constants
pi = math.pi
e = math.e

constants = {"e": e, "pi": pi}


# commands
def addv(*args, **kwargs):
    """"command to add global variable"""
    if all_names.__contains__(kwargs.get("name")) or all_names.__contains__(args[0]):
        raise Exception("name already exists")
    if kwargs.keys().__contains__("name"):
        name = str(kwargs.get("name"))
    elif len(args) >= 2:
        name = str(args[0])
    else:
        raise Exception("name missing")
    if kwargs.keys().__contains__("value"):
        value = str(kwargs.get("value"))
    elif len(args) >= 2:
        value = str(args[1])
    else:
        raise Exception("no value")
    if re.fullmatch(number_pattern, value):
        value = f.var_from_str(value)
    elif re.fullmatch(exec_pattern, value):
        func = f.Node.init_root("f", value, [])
        value = func(*func.nodes)
    else:
        raise Exception("value is not a number")
    name = str(name)
    if re.fullmatch(name_pattern, name):
        vars.update({name: value})
        all_names.append(name)
    else:
        raise Exception("bad name pattern")


def addf(*args, **kwargs):
    """"command add global function"""
    if kwargs.keys().__contains__("name") and not all_names.__contains__(kwargs.get("name")):
        name = kwargs.get("name")
    elif len(args) >= 3 and not all_names.__contains__(args[0]):
        name = args[0]
    else:
        raise Exception("no name or such name exists")
    if kwargs.keys().__contains__("func"):
        func = kwargs.get("func")
    elif len(args) >= 3:
        func = args[-1]
    else:
        raise Exception("no function")
    params = [(k, v) for k, v in kwargs.items() if re.fullmatch(param_pattern, k)]
    params.sort(key=lambda x: x[0])
    # params.append(args[1:-1])
    for i in range(1, len(args) - 1):
        params.append(args[i])
    if len(params) == 0:
        raise Exception("no function arguments")
    name = str(name)
    if re.fullmatch(name_pattern, name):
        function = f.Node.init_root(name, func, params)
        u_funs.update({name: (function, len(params))})
        all_names.append(name)
    else:
        raise Exception("bad name pattern")


def close(*args, **kwargs):
    """"command to exit program"""
    sys.exit()


def ls(*args, **kwargs):
    """"command to list global collections"""
    if len(args) >= 1 and data.keys().__contains__(args[0]):
        __format(data.get(args[0]))
        return
    elif kwargs.keys().__contains__("data") and data.keys().__contains__(kwargs.get("data")):
        __format(data.get(kwargs.get("data")))
    else:
        raise Exception("collection does not exist")
    return


def rmf(*args, **kwargs):
    """removes user defined function"""
    if kwargs.keys().__contains__("name") and u_funs.get(kwargs.get("name")) is not None:
        # all_names.remove(kwargs.get("name"))
        name = kwargs.get("name")
        # u_funs.pop(kwargs.get("name"), None)
    elif u_funs.get(args[0]) is not None:
        # all_names.remove(args[0])
        name = args[0]
        # u_funs.pop(args[0], None)
    else:
        raise Exception("function does not exist")
    name = str(name)
    if re.fullmatch(name_pattern, name):
        all_names.remove(name)
        u_funs.pop(name, None)
    else:
        raise Exception("bad name pattern")


def rmv(*args, **kwargs):
    """removes variable"""
    if kwargs.keys().__contains__("name") and vars.get(kwargs.get("name")) is not None:
        name = kwargs.get("name")
        # all_names.remove(kwargs.get("name"))
        # vars.pop(kwargs.get("name"), None)
    elif vars.get(args[0]) is not None:
        name = args[0]
        # all_names.remove(args[0])
        # vars.pop(args[0], None)
    else:
        raise Exception("variable does not exist")
    name = str(name)
    if re.fullmatch(name_pattern, name):
        all_names.remove(name)
        vars.pop(name, None)
    else:
        raise Exception("bad name pattern")


def save(*args, **kwargs):
    if kwargs.keys().__contains__("file"):
        name = kwargs.get("file")
    elif args[0] is not None:
        name = args[0]
    else:
        raise Exception("need file name without extension")
    with open("saved/" + name + '.pickle', 'wb') as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    print("saved to file: ./saved/" + name + ".pickle")


def load(*args, **kwargs):
    global data
    global all_names
    global built_ins
    global constants
    global funs
    global u_funs
    global vars
    if kwargs.keys().__contains__("file"):
        name = kwargs.get("file")
    elif args[0] is not None:
        name = args[0]
    else:
        raise Exception("need file name without extension")
    with open("saved/" + name + '.pickle', 'rb') as f:
        data = pickle.load(f)
        all_names = data.get("na")
        built_ins = data.get("bi")
        constants = data.get("const")
        funs = data.get("func")
        u_funs = data.get("udf")
        vars = data.get("var")
    print("loaded file: ./saved/" + name + ".pickle")


# private
def __format(container):
    """"format formating output for ls command"""
    count = 1
    if isinstance(container, list):
        for c in container:
            print(f"{count:<{3}} {str(c):<{50}}")
            count += 1
    elif isinstance(container, dict):
        for k, v in zip(container.keys(), container.values()):
            if isinstance(v, tuple) and isinstance(v[0], f.Node):
                print(f"{count:<{3}} {k:{10}} <- {str(v[0]):<{50}}")
            else:
                print(f"{count:<{3}} {k:{10}} <- {str(v):<{50}}")
            count += 1


built_ins = {"addv": addv, "addf": addf, "close": close, "exit": close, "quit": close, "ls": ls, "load": load, "rmf": rmf, "rmv": rmv, "save": save}
# built_ins_names = [b.__name__ for b in built_ins]
all_names = []
data = {"na": all_names, "bi": built_ins, "const": constants, "func": funs, "udf": u_funs, "var": vars}
data.update({"data": data})


def __collect_names():
    """"collects hard coded functions, etc."""
    for c in constants.keys():
        if not all_names.__contains__(c):
            all_names.append(c)
    for c in u_funs.keys():
        if not all_names.__contains__(c):
            all_names.append(c)
    for c in vars.keys():
        if not all_names.__contains__(c):
            all_names.append(c)
