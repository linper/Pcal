import math
import sys
import re
import function as f
import pickle
import temp_pool as tp
import lst as l

param_pattern = re.compile(r"p[\d]+")
number_pattern = re.compile(r"(^(0[bB])[01]+$)|(^(0[oO])[0-7]+$)|(^(0[xX])[0-9a-fA-F]+$)|(^[-+]?[0-9]*$)|(^[-+]?"
                            r"[0-9]*\.[0-9]+$)|(^[-+]?[0-9]*\.?[0-9]+e[-+]?[0-9]+$)")
exec_pattern = re.compile(r"^([\w\d_]+(\([\w\d\s_]+\)))+|([\w\d()+*\-/.,<>^=%!|&\"_]+)\s*$")
name_pattern = re.compile(r"^[a-zA-Z_][\w_]*")

u_funs = {}
vars = {}
lsts = {}


# functions
def b_or(*args):
    return int(bool(args[0]) or bool(args[1]))


def b_and(*args):
    return int(bool(args[0]) and bool(args[1]))


def b_xor(*args):
    return int(bool(args[0]) != bool(args[1]))


def b_eq(*args):
    return int(args[0] == args[1])


def b_not(*args):
    if len(args) == 1:
        return int(not bool(args[0]))
    elif len(args) == 2:
        return int(args[0] != args[1])


def gt(*args):
    return int(args[0] > args[1])


def ge(*args):
    return int(args[0] >= args[1])


def lt(*args):
    return int(args[0] < args[1])


def le(*args):
    return int(args[0] <= args[1])


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


funs = {"|": (b_or, 2), "&": (b_and, 2), "^": (b_xor, 2), "==": (b_eq, 2), "!=": (b_not, 2), "!": (b_not, 1),
        "<": (lt, 2), "<=": (le, 2), ">": (gt, 2), ">=": (ge, 2),
        "+": (sum, 256), "-": (sub, 256), "/": (div, 256), "*": (mul, 256), "**": (pow, 32),
        "or": (b_or, 2), "and": (b_and, 2), "xor": (b_xor, 2), "eq": (b_eq, 2), "nq": (b_not, 2), "not": (b_not, 1),
        "lt": (lt, 2), "le": (le, 2), "gt": (gt, 2), "ge": (ge, 2),
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
        value = f.execute(func)
    else:
        raise Exception("value is not a number")
    name = str(name)
    if re.fullmatch(name_pattern, name):
        vars.update({name: value})
        all_names.append(name)
    else:
        raise Exception("bad name pattern")


def addf(*args, **kwargs):
    """"command to add global function"""
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


def addl(*args, **kwargs):
    """"command to add global list"""
    lst = None
    if kwargs.keys().__contains__("name") and not all_names.__contains__(kwargs.get("name")):
        name = kwargs.get("name")
    elif len(args) >= 2 and not all_names.__contains__(args[0]):
        name = args[0]
    else:
        raise Exception("no name or such name exists")
    if isinstance(args[1][0], str):
        _, list_comps = l.separate_list_comp(" ".join(args[1: len(args)]), clean=True)
        if len(list_comps) == 1:
            lst = l.make_list(list_comps[0])
    elif kwargs.keys().__contains__("list"):
        lst = kwargs.get("list")
    elif len(args) >= 2:
        lst = args[-1]
    else:
        raise Exception("no list")
    if not isinstance(lst, list):
        raise Exception("value is not a list")
    name = str(name)
    if re.fullmatch(name_pattern, name):
        lsts.update({name: lst})
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


def rm(*args, **kwargs):
    """removes user defined function or variable"""
    if kwargs.keys().__contains__("name") and u_funs.get(kwargs.get("name")) is not None:
        name = kwargs.get("name")
    elif u_funs.get(args[0]) is not None:
        name = args[0]
    elif vars.get(args[0]) is not None:
        name = args[0]
    elif lsts.get(args[0]) is not None:
        name = args[0]
    else:
        raise Exception("function or variable does not exist")
    name = str(name)
    if re.fullmatch(name_pattern, name):
        if vars.get(name) is not None:
            vars.pop(name, None)
        elif lsts.get(name) is not None:
            lsts.pop(name, None)
        else:
            u_funs.pop(name, None)
        all_names.remove(name)
    else:
        raise Exception("bad name pattern")


def save(*args, **kwargs):
    """saves current daa to file"""
    if kwargs.keys().__contains__("file"):
        name = kwargs.get("file")
    elif args[0] is not None:
        name = args[0]
    else:
        raise Exception("need file name without extension")
    with open("saved/" + name + '.pickle', 'wb') as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    print("saved to file: ./saved/" + name + ".pkl")


def load(*args, **kwargs):
    """"loads data from file"""
    global data
    global all_names
    global commands
    global constants
    global funs
    global u_funs
    global vars
    global lsts
    if kwargs.keys().__contains__("file"):
        name = kwargs.get("file")
    elif args[0] is not None:
        name = args[0]
    else:
        raise Exception("need file name without extension")
    with open("saved/" + name + '.pickle', 'rb') as f:
        data = pickle.load(f)
        all_names = data.get("na")
        commands = data.get("cmd")
        constants = data.get("const")
        funs = data.get("func")
        u_funs = data.get("udf")
        vars = data.get("var")
        lsts = data.get("lst")
    print("loaded file: ./saved/" + name + ".pkl")


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


commands = {"addv": addv, "addf": addf, "addl": addl, "close": close, "exit": close, "quit": close, "ls": ls, "load": load, "rm": rm, "save": save}
all_names = ["if", "else", "for", "in"]
data = {"na": all_names, "cmd": commands, "const": constants, "func": funs, "udf": u_funs, "var": vars, "lst": lsts}
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
