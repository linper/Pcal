import math
from sys import exit
import re
import function as f
import pickle
import lst as l
import os

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
    args = __flatten_args(args)
    return int(bool(args[0]) or bool(args[1]))


def b_and(*args):
    args = __flatten_args(args)
    return int(bool(args[0]) and bool(args[1]))


def b_xor(*args):
    args = __flatten_args(args)
    return int(bool(args[0]) != bool(args[1]))


def b_eq(*args):
    args = __flatten_args(args)
    return int(args[0] == args[1])


def b_not(*args):
    args = __flatten_args(args)
    if len(args) == 1:
        return int(not bool(args[0]))
    elif len(args) == 2:
        return int(args[0] != args[1])


def gt(*args):
    args = __flatten_args(args)
    return int(args[0] > args[1])


def ge(*args):
    args = __flatten_args(args)
    return int(args[0] >= args[1])


def lt(*args):
    args = __flatten_args(args)
    return int(args[0] < args[1])


def le(*args):
    args = __flatten_args(args)
    return int(args[0] <= args[1])


def sum(*args):
    args = __flatten_args(args)
    s = 0.0
    for i in range(len(args)):
        s += args[i]
    return s


def sub(*args):
    args = __flatten_args(args)
    s = float(args[0])
    for i in range(1, len(args)):
        s -= args[i]
    return s


def div(*args):
    args = __flatten_args(args)
    s = float(args[0])
    for i in range(1, len(args)):
        s /= args[i]
    return s


def mod(*args):
    args = __flatten_args(args)
    s = float(args[0])
    for i in range(1, len(args)):
        s %= args[i]
    return s


def mul(*args):
    args = __flatten_args(args)
    s = 1.0
    for i in range(len(args)):
        s *= args[i]
    return s


def pow(*args):
    args = __flatten_args(args)
    s = float(args[0])
    for i in range(1, len(args)):
        s **= args[i]
    return s


def ln(*args):
    args = __flatten_args(args)
    return math.log(math.e, args[0])


def log10(*args):
    args = __flatten_args(args)
    return math.log(10, args[0])


def log2(*args):
    args = __flatten_args(args)
    return math.log(2, args[0])


def log(*args):
    args = __flatten_args(args)
    return math.log(args[1], args[0])


def abs(*args):
    args = __flatten_args(args)
    return math.fabs(args[0])


def tan(*args):
    args = __flatten_args(args)
    return math.tan(args[0])


def atan(*args):
    args = __flatten_args(args)
    return math.atan(args[0])


def sin(*args):
    args = __flatten_args(args)
    return math.sin(args[0])


def asin(*args):
    args = __flatten_args(args)
    return asin(args[0])


def cos(*args):
    args = __flatten_args(args)
    return math.cos(args[0])


def acos(*args):
    args = __flatten_args(args)
    return math.acos(args[0])


def rad(*args):
    return math.radians(args[0])


def deg(*args):
    return math.degrees(args[0])


def floor(*args):
    return math.floor(args[0])


def ceil(*args):
    return math.ceil(args[0])


def forward(*args):
    return args[0]


def _range(*args):
    args = __flatten_args(args)
    if len(args) == 1:
        return list(range(args[0]))
    elif len(args) == 2:
        return list(range(args[0], args[1]))
    else:
        return list(range(args[0], args[1], args[2]))


def subl(ls, start=0, end=None, step=1):
    if end is None:
        end = len(ls)
    if start is None:
        start = 0
    if step is None:
        step = 1
    return ls[start:end:step]


def mean(*args):
    args = __flatten_args(args)
    _sum = 0.0
    for item in args:
        _sum += item.data
    return _sum / len(args)


def length(*args):
    return len(__flatten_args(args))


def cat(*args):
    return __flatten_args(args)


def fill(*args):
    if isinstance(args[0], list):
        for i in range(len(args[0])):
            args[0][i].data = args[1]
        return args[0]
    else:
        new_list = []
        for i in range(args[0]):
            new_list.append(f.nodefy(args[1]))
        return new_list


def _str(*args):
    new_str = ""
    for a in args:
        new_str = new_str + str(a).replace(" ", "_")
    return new_str


list_funs = [subl, forward, fill]  # iterable arguments will not be flattened
funs = {"|": (b_or, 2), "&": (b_and, 2), "^": (b_xor, 2), "==": (b_eq, 2), "!=": (b_not, 2), "!": (b_not, 1),
        "<": (lt, 2), "<=": (le, 2), ">": (gt, 2), ">=": (ge, 2),
        "+": (sum, 4096), "-": (sub, 4096), "/": (div, 4096), "%": (mod, 4096), "*": (mul, 4096), "**": (pow, 32),
        "or": (b_or, 2), "and": (b_and, 2), "xor": (b_xor, 2), "eq": (b_eq, 2), "nq": (b_not, 2), "not": (b_not, 1),
        "lt": (lt, 2), "le": (le, 2), "gt": (gt, 2), "ge": (ge, 2),
        "sum": (sum, 4096), "sub": (sub, 4096), "div": (div, 4096), "mod": (mod, 4096), "mul": (mul, 4096), "pow": (pow, 64), "abs": (abs, 1),
        "tan": (tan, 1), "atan": (atan, 1), "sin": (sin, 1), "asin": (asin, 1), "cos": (cos, 1), "acos": (acos, 1),
        "ln": (ln, 1), "log2": (log2, 1), "log10": (log10, 1), "log": (log, 2),
        "rad": (rad, 1), "deg": (deg, 1),
        "floor": (floor, 1), "ceil": (ceil, 1),
        "forward": (forward, 1), "subl": (subl, 4), "range": (_range, 3), "len": (length, float("inf")), "cat": (cat, float("inf")),
        "fill": (fill, 2), "str": (_str, 4096), "mean": (mean, 4096)}

# constants
pi = math.pi
e = math.e

constants = {"e": e, "pi": pi}


# commands
def addv(*args, **kwargs):
    """"command to add global dynamic variable"""
    override = False
    if all_names.__contains__(kwargs.get("name")) or all_names.__contains__(args[0]):
        if not vars.__contains__(kwargs.get("name")) and not vars.__contains__(args[0]):
            raise Exception("name already exists, and it can't be overridden")
        else:
            override = True
            print("variable will be overridden")
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
        if not override:
            value_node = f.Node(value, name=name)
        else:
            value_node = vars.get(name)
            value_node.data = value
            value_node.name = str(value)
    elif re.fullmatch(exec_pattern, value):
        value = f.Node.init_root("f", value, [])
        value_executed = f.execute(value)
        if isinstance(value_executed, list):
            return addl(name, value_executed)
        if not override:
            value_node = f.Node(value, name=name)
        else:
            value_node = vars.get(name)
            value_node.data = value
            value_node.name = str(value)
    else:
        raise Exception("value is not a number")
    name = str(name)
    if re.fullmatch(name_pattern, name):
        vars.update({name: value_node})
        if not all_names.__contains__(name):
            all_names.append(name)
        return value
    else:
        raise Exception("bad name pattern")


def addcv(*args, **kwargs):
    """"command to add global static variable"""
    override = False
    if all_names.__contains__(kwargs.get("name")) or all_names.__contains__(args[0]):
        if not vars.__contains__(kwargs.get("name")) and not vars.__contains__(args[0]):
            raise Exception("name already exists, and it can't be overridden")
        else:
            override = True
            print("variable will be overridden")
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
        if not override:
            value_node = f.Node(value, name=name)
        else:
            value_node = vars.get(name)
            value_node.data = value
            value_node.name = str(value)
    elif re.fullmatch(exec_pattern, value):
        func = f.Node.init_root("f", value, [])
        value = f.execute(func)
        if not override:
            value_node = f.Node(value, name=name)
        else:
            value_node = vars.get(name)
            value_node.data = value
            value_node.name = str(value)
        if isinstance(value, list):
            return addl(name, value)
    else:
        raise Exception("value is not a number")
    name = str(name)
    if re.fullmatch(name_pattern, name):
        vars.update({name: value_node})
        if not all_names.__contains__(name):
            all_names.append(name)
        return value
    else:
        raise Exception("bad name pattern")


def addf(*args, **kwargs):
    """"command to add global function"""
    if kwargs.keys().__contains__("name") and \
            (not all_names.__contains__(kwargs.get("name")) or u_funs.__contains__(kwargs.get("name"))):
        if u_funs.__contains__(kwargs.get("name")):
            print("function " + str(kwargs.get("name")) + " will be overridden")
        name = kwargs.get("name")
    elif len(args) >= 3 and (not all_names.__contains__(args[0]) or u_funs.__contains__(args[0])):
        if u_funs.__contains__(args[0]):
            print("function " + str(kwargs.get("name")) + " will be overridden")
        name = args[0]
    else:
        raise Exception("name missing")
    if kwargs.keys().__contains__("func"):
        func = kwargs.get("func")
    elif len(args) >= 3:
        func = args[-1]
    else:
        raise Exception("no function")
    params = [(k, v) for k, v in kwargs.items() if re.fullmatch(param_pattern, k)]
    params.sort(key=lambda x: x[0])
    for i in range(1, len(args) - 1):
        params.append(args[i])
    if len(params) == 0:
        raise Exception("no function arguments")
    name = str(name)
    if re.fullmatch(name_pattern, name):
        function = f.Node.init_root(name, func, params)
        u_funs.update({name: (function, len(params))})
        all_names.append(name)
        return function.name
    else:
        raise Exception("bad name pattern")


def addl(*args, **kwargs):
    """"command to add global dynamic list"""
    lst = None
    if kwargs.keys().__contains__("name") and \
            (not all_names.__contains__(kwargs.get("name")) or lsts.__contains__(kwargs.get("name"))):
        if lsts.__contains__(kwargs.get("name")):
            print("list " + str(kwargs.get("name")) + " will be overridden")
        name = kwargs.get("name")
    elif len(args) >= 2 and (not all_names.__contains__(args[0]) or lsts.__contains__(args[0])):
        if lsts.__contains__(args[0]):
            print("list " + str(kwargs.get("name")) + " will be overridden")
        name = args[0]
    else:
        raise Exception("name missing")
    if isinstance(args[1], str):
        _, list_comps = l.separate_list_comp(" ".join(args[1: len(args) - 1]), clean=True)
        if len(list_comps) == 1:
            lst = l.make_list(list_comps[0], args[-1])
    elif kwargs.keys().__contains__("list"):
        lst = kwargs.get("list")
    elif len(args) >= 2:
        lst = args[1]
    else:
        raise Exception("no list")
    if not isinstance(lst, list):
        raise Exception("value is not a list")
    else:
        node_list = []
        for item in lst:
            if isinstance(item, f.Node):
                node_list.append(item)
            else:
                l.make_list_node(node_list, item)
    name = str(name)
    if re.fullmatch(name_pattern, name):
        lsts.update({name: node_list})
        all_names.append(name)
        return node_list
    else:
        raise Exception("bad name pattern")


def addcl(*args, **kwargs):
    """"command to add global static list"""
    lst = None
    if kwargs.keys().__contains__("name") and \
            (not all_names.__contains__(kwargs.get("name")) or lsts.__contains__(kwargs.get("name"))):
        if lsts.__contains__(kwargs.get("name")):
            print("list " + str(kwargs.get("name")) + " will be overridden")
        name = kwargs.get("name")
    elif len(args) >= 2 and (not all_names.__contains__(args[0]) or lsts.__contains__(args[0])):
        if lsts.__contains__(args[0]):
            print("list " + str(kwargs.get("name")) + " will be overridden")
        name = args[0]
    else:
        raise Exception("name missing")
    if isinstance(args[1], str):
        _, list_comps = l.separate_list_comp(" ".join(args[1: len(args) - 1]), clean=True)
        if len(list_comps) == 1:
            lst = l.make_list(list_comps[0], args[-1])
    elif kwargs.keys().__contains__("list"):
        lst = kwargs.get("list")
    elif len(args) >= 2:
        lst = args[1]
    else:
        raise Exception("no list")
    if not isinstance(lst, list):
        raise Exception("value is not a list")
    else:
        node_list = []
        for item in lst:
            if isinstance(item, f.Node):
                node_list.append(item)
            else:
                l.make_list_node(node_list, item)
    name = str(name)
    if re.fullmatch(name_pattern, name):
        lsts.update({name: node_list})
        all_names.append(name)
        return node_list
    else:
        raise Exception("bad name pattern")


def close(*args, **kwargs):
    """"command to exit program"""
    exit(0)


def ls(*args, **kwargs):
    """"command to list global collections"""
    if len(args) >= 1 and data.keys().__contains__(args[0]):
        __format(data.get(args[0]))
        return None
    elif kwargs.keys().__contains__("data") and data.keys().__contains__(kwargs.get("data")):
        __format(data.get(kwargs.get("data")))
        return None
    else:
        raise Exception("collection does not exist")


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
        return None
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
    path = os.path.abspath(os.path.split(os.path.abspath(__file__))[0] + "/saved/" + name + '.pkl')
    with open(path, 'wb') as f:
        pickle.dump([u_funs, vars, lsts], f, pickle.HIGHEST_PROTOCOL)
    print("saved to file: " + path)
    return None


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
    global all_names
    all_names = all_names_default.copy()
    if kwargs.keys().__contains__("file"):
        name = kwargs.get("file")
    elif args[0] is not None:
        name = args[0]
    else:
        raise Exception("need file name without extension")
    path = os.path.abspath(os.path.split(os.path.abspath(__file__))[0] + "/saved/" + name + '.pkl')
    with open(path, 'rb') as f:
        _data = pickle.load(f)
        u_funs = _data[0]
        data.update({"udf": u_funs})
        vars = _data[1]
        data.update({"var": vars})
        lsts = _data[2]
        data.update({"lst": lsts})
        __collect_names()
    print("loaded file: " + path)
    return None


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


commands = {"addv": addv, "addcv": addcv, "addf": addf, "addl": addl, "addcl": addcl, "close": close, "exit": close, "quit": close, "ls": ls, "load": load, "rm": rm, "save": save}
all_names = ["if", "else", "for", "in"]
all_names_default = ["if", "else", "for", "in"]
data = {"na": all_names, "cmd": commands, "const": constants, "func": funs, "udf": u_funs, "var": vars, "lst": lsts}
data.update({"data": data})
cmd_func = ["addl"]


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
    for c in lsts.keys():
        if not all_names.__contains__(c):
            all_names.append(c)
    for c in funs.keys():
        if not all_names.__contains__(c):
            all_names.append(c)
    for c in commands.keys():
        if not all_names.__contains__(c):
            all_names.append(c)


def __flatten_args(*args):
    new_args = []
    for a in args[0]:
        if isinstance(a, (list, set, tuple)):
            for a_it in a:
                new_args.append(a_it)
        else:
            new_args.append(a)
    return new_args
