import exec
import re
import temp_pool as tp
import lst


number_pattern = re.compile(r"(^(0[bB])[01]+$)|(^(0[oO])[0-7]+$)|(^(0[xX])[0-9a-fA-F]+$)|(^[-+]?[0-9]*$)|(^[-+]?"
                            r"[0-9]*\.[0-9]+$)|(^[-+]?[0-9]*\.?[0-9]+e[-+]?[0-9]+$)")
list_exec_pattern = re.compile(r"^[(\]][\w\s(){}@$;\[\]+*\-/.,<>^%=!|&\"_]+[\])]\s*$")
binary_pattern = re.compile(r"(^(0[bB])[01]+$)")
octal_pattern = re.compile(r"(^(0[oO])[0-7]+$)")
hexadecimal_pattern = re.compile(r"(^(0[xX])[0-9a-fA-F]+$)")
integer_pattern = re.compile(r"(^[-+]?[0-9]*$)")
float_pattern = re.compile(r"(^[-+]?[0-9]*\.[0-9]+$)")
std_pattern = re.compile(r"(^[-+]?[0-9]*\.?[0-9]+e[-]?[0-9]+$)")
std_enhanced_pattern = re.compile(r"([-]?[\w\d_.#]+e[-]?[\w\d_.#]+)")
levels = [r"(?:>=)", r">", r"(?:<=)", r"<", r"(?:!=)", r"(?:==)", r"\|", r"\&", r"\^", r"\+", r"[\w\d_#]-", r"[^*](\*)[^*]", r"\/", r"%", r"(?:\*\*)", r"[\d\w_]+#"]
level_str = [">=", ">", "<=", "<", "!=", "==", "|", "&", "^", "+", "-", "*", "/", "%", "**", ""]
# levels = [r"(?:>=)", r">", r"(?:<=)", r"<", r"(?:!=)", r"(?:==)", r"\|", r"\&", r"\^", r"\+", r"[\w\d_#]-", r"^-+[\w#_]", r"[^*](\*)[^*]", r"\/", r"%", r"(?:\*\*)", r"[\d\w_]+#"]
# level_str = [">=", ">", "<=", "<", "!=", "==", "|", "&", "^", "+", "-", "-", "*", "/", "%", "**", ""]
basic_multi = re.compile(r"-?[\w\d_.,]+")
basic = re.compile(r"-?[\w\d_.]+")
func_pattern = re.compile(r"[\d\w_]*#")
single_eq_pattern = re.compile(r"[^!<>=](?:=)[^=]")
bad_eq_pattern = re.compile(r"^[=]")
operators = re.compile(r"[><+=|&^*/%!]")

class Node:
    """node of function tree"""
    def __init__(self, data=None, params=None, name=None):
        if params is None:
            params = dict()
        self.data = data
        self.name = name
        self.nodes = []
        self.parameters = params
        self.data_as_str = None

    @classmethod
    def init_root(cls, name, data, params, strict=True, superss=False):
        """"__init__for root node"""
        root = Node()
        root.name = name
        root.data_as_str = str(data)
        if isinstance(params, dict):
            root.parameters = params
        else:
            for i in range(len(params) * strict):
                if not re.search(r"(?:(?:[(,+\-*|&/><=^])|(?:^))" + params[i] + r"(?:(?:[),+\-*|&/><=^])|(?:$))", root.data_as_str) and not superss:
                    if not superss:
                        raise Exception(f"there is no \"{params[i]}\" in function: {data}")
                    else:
                        continue
                else:
                    root.parameters.update({params[i]: params[i]})
        init_tree(root, data, 0, root.parameters)
        return root

    def __str__(self): # todo list printing format is horible
        if len(self.parameters.keys()) != 0 and self.name is not None:
            return f"{self.name}{list(self.parameters.keys())}: {self.data_as_str}"
        elif self.data_as_str is not None and self.name is not None:
            return f"{self.name}: {self.data_as_str}"
        elif self.name is not None:
            return f"{self.name}: {self.data}"
        else:
            return f"{self.data}"

    def __contains__(self, item):
        if self.data == item:
            return True
        elif len(self.nodes) != 0:
            for n in self.nodes:
                if n.__contains__(item):
                    return True
        return False

    def __call__(self, *args, **kwargs):
        """"function tree execution entry point"""
        d = {}
        if isinstance(self.data, Node):
            for k, n in zip(self.data.parameters.keys(), self.nodes):
                d.update({k: iterate(n, args[0])})
            return self.data(d)
        elif not isinstance(args[0], dict):
            for k, n in zip(self.parameters.keys(), args):
                if isinstance(n, Node):
                    d.update({k: iterate(n, {})})
                else:
                    d.update({k: n})
            return iterate(self, d)
        else:
            return iterate(self, args[0])


def execute(root):
    """"function tree execution entry point"""
    if isinstance(root, (int, float, str)):
        return root
    d = {}
    if isinstance(root.data, Node):
        for k, v in zip(root.data.parameters.keys(), root.nodes):
            d.update({k: iterate(v, {})})
        return root.data(d)
    else:
        return iterate(root, d)


def iterate(root, params):
    """"one iteration of recursive function execution"""
    if isinstance(root, Node) and isinstance(root.data, Node) and exec.u_funs.get(root.data.name) is not None:
        return root(params)
    if len(root.nodes) != 0:
        l = []
        for n in root.nodes:
            l.append(iterate(n, params))
        if isinstance(root.data, list):
            return root.data[int(l[0])]
        l = [execute(item) if isinstance(item, Node) else item for item in l]
        return root.data(*l)
    elif params.keys().__contains__(str(root.data)):
        return params.get(str(root.data))
    elif isinstance(root.data, (int, float, str)):
        return root.data
    elif isinstance(root.data, list):
        return [iterate(d, {}) for d in root.data]
    else:
        return iterate(root.data, {})


def nodefy(value, params=None):
    """"if value is not a Node turns it to Node"""
    if value is None:
        return None
    if params is None:
        params = {}
    if not isinstance(value, Node):
        value = Node(value, params=params)
    return value


def init_tree(root, data, level, params):
    """"creates inner function"""
    data = swap_std_exp(data, params)
    data = parse_pluses_minuses(data)
    leftover, funcs = strip_functions(data, "([", ")]", "#")
    leftover = leftover.replace("@", "")
    return pass_levels(root, leftover, funcs, level, params)


def pass_levels(parent, data, inner, level, params):
    """"creates new node for function(recursive) separated by operators"""
    inner_taken = 0
    strings, func, tree = get_level(data, level)
    if func is not None:
        max_nodes = func[1]
        parent.data = func[0]
        if tree:
            f_data, f_list = strip_functions(inner[0], "([", ")]", "#")
            f_data = re.split(r",", f_data)
            funs = dress_up_functions(f_data, f_list)
            if count_nodes(func[0], funs, params) > max_nodes:
                raise Exception("out of nodes")
            for i in range(len(funs)):
                if re.fullmatch(basic_multi, funs[i]):
                    add_single(parent, funs[i], params)
                elif funs[i] == "":
                    parent.nodes.append(Node(None, params=params))
                elif re.fullmatch(list_exec_pattern, funs[i]):
                    funs[i] = "[" + funs[i][1:len(funs[i])-1] + "]"
                    parent.nodes.append(Node(data=lst.make_list(lst.separate_list_comp(funs[i], clean=True)[1][0], []), params=params, name=funs[i]))
                else:
                    parent.nodes.append(init_tree(Node(params=params, name=funs[i]), funs[i], 0, params))
            return parent
    else:
        raise Exception("function not found")
    if len(strings) != 0:
        for string in strings:
            inner_count = len(re.findall(func_pattern, string))
            if re.fullmatch(basic_multi, string):
                simple = True
            else:
                if string == "#":
                    inner_taken += 1
                    parent.nodes.append(init_tree(Node(params=params, name=inner[inner_taken - 1]), inner[inner_taken - 1], 0, params))
                    continue
                simple = False
            if len(parent.nodes) < max_nodes - 1:
                if simple:
                    add_single(parent, string, params)
                else:
                    inner_taken += inner_count
                    new_node = pass_levels(Node(params=params, name=string), string, inner[inner_taken - inner_count: inner_taken], level + 1, params)
                    parent.nodes.append(new_node)
            elif len(parent.nodes) + 1 == max_nodes:
                if simple:
                    add_single(parent, string, params)
                else:
                    inner_taken += inner_count
                    parent.nodes.append(pass_levels(Node(params=params, name=string), string, inner[inner_taken - inner_count: inner_taken], level, params))
            else:
                raise Exception("out of nodes")
        return parent
    else:
        parent.nodes.append(init_tree(Node(params=params, name=inner[0]), inner[0], 0, params))
        return parent


def add_single(parent, data, params):
    """"adds comma separated non functional nodes to function tree"""
    data.strip(',')
    par = re.split(r",", data)
    for p in par:
        result = nodefy(var_from_str(p, params, node_return=True), params=params)
        parent.nodes.append(result)


def get_level(data, level):
    """"gets separator function, other stuff"""
    data = str(data)
    matcher = level_str[0]
    tree = False
    changed = False
    for l in range(level, len(levels)):
        if bool(re.search(levels[l], data)):
            level = l
            matcher = level_str[l]
            changed = True
            break
    fixed = []
    if level + 1 < len(levels):
        if re.search(single_eq_pattern, data):
            raise Exception("single equality sign not allowed")
        strings = data.replace(" ", "").split(matcher)
        for s in strings:
            if re.match(bad_eq_pattern, s):
                raise Exception("bad (not)equality pattern")
        if matcher == "-":
            new_str = [strings[0]]
            for s in strings[1:]:
                if re.match(operators, new_str[-1][-1]):
                    new_str[-1] = "".join([new_str[-1], "-", s])
                else:
                    new_str.append(s)
            strings = new_str
        if strings.__contains__(""):
            count = 0
            is_empty = False
            if ["+", "|", "&", "^", "<", ">"].__contains__(matcher):
                if strings.__contains__(""):
                    raise Exception("excess of operators")
            elif matcher == "*":
                for i in range(len(strings)):
                    if strings[i] == "":
                        is_empty = True
                        count += 1
                    elif is_empty:
                        is_empty = False
                        if count > 1:
                            raise Exception("Syntax error")
                        count = 0
                    if strings[i] != "" and (len(strings) == 1 or
                                                             (i == 0 and strings[i + 1] != "") or
                                                             (i == len(strings) - 1 and strings[i - 1] != "") or
                                                             (strings[i - 1] != "" and strings[i + 1] != "")):
                        fixed.append(strings[i])
                    elif strings[i] == "":
                        fixed.append(str(strings[i - 1] + matcher + matcher + strings[i + 1]))
            else:
                raise Exception("Syntax error")
        else:
            fixed = strings
        if changed:
            func = exec.data.get("func").get(level_str[level])
        else:
            func = exec.data.get("func").get("forward")
    else:
        s = str(re.search(levels[level], data).group()).strip('#')
        if exec.data.get("func").keys().__contains__(s):
            func = exec.data.get("func").get(s)
        elif tp.temps.keys().__contains__(s):
            func = tp.temps.get(s)
        elif exec.data.get("lst").keys().__contains__(s):
            lst = exec.data.get("lst").get(s)
            func = lst, len(lst)
        else:
            func = exec.data.get("udf").get(s)
        tree = True
    return fixed, func, tree


def strip_functions(data, o_sequence, c_sequence, replacement):
    """"strips function of brackets and replaces them with #"""
    fun_list = []
    l_indices = [i for i, ltr in enumerate(data) if o_sequence.__contains__(ltr)]
    r_indices = [i for i, ltr in enumerate(data) if c_sequence.__contains__(ltr)]
    if len(l_indices) != len(r_indices):
        raise Exception("wrong number of \"" + o_sequence + " " + c_sequence + "\"")
    f_list = []
    if len(l_indices) > 0:
        l_par_count = r_par_count = 1
        l_index = 0
        r_index = 0
        l_bound = l_indices[0]
        r_bound = r_indices[0]
        while l_par_count <= len(l_indices) or r_par_count <= len(r_indices):
            if l_par_count == r_par_count > 0 and (l_index + 1 == len(l_indices) or l_indices[l_index + 1] > r_bound):
                fun_list.append(data[l_bound: r_bound + 1])
                if l_par_count == len(l_indices) or r_par_count == len(r_indices):
                    break
                if l_index + 1 != len(l_indices):
                    l_index += 1
                    l_par_count = l_index + 1
                    r_index += 1
                    r_par_count = r_index + 1
                    l_bound = l_indices[l_index]
                    r_bound = r_indices[r_index]
                continue
            elif l_par_count < r_par_count:
                raise Exception("wrong order of opening and closing elements")
            if l_par_count < len(l_indices) and l_indices[l_index + 1] < r_indices[r_index]:
                l_index += 1
                l_par_count += 1
            elif r_par_count < len(r_indices):
                r_index += 1
                r_par_count += 1
                r_bound = r_indices[r_index]
        for s in fun_list:
            data = data.replace(s, replacement, 1)
        for s in fun_list:
            f_list.append(s[1: -1])
    return data, f_list


def dress_up_functions(h_string_arr, inner, swap_char='#'):
    """"opposite of 'strip_functions' but returns array of functions, if used with'strip_functions' can separate
    comma separated functions"""
    function_arr = []
    count = 0
    for f in h_string_arr:
        fun = ""
        for c in f:
            if c == swap_char:
                fun = fun + "(" + inner[count] + ")"
                count += 1
            else:
                fun = fun + c
        function_arr.append(fun)
    return function_arr


def var_from_str(data, params=None, force_ex=True, node_return=False):
    """"parses variable, constant-variable or non_decimal system number to number"""
    sign = 1
    if len(data) != 0 and data[0] == '-':
        sign = -1
    if re.match(r"[+-]", data):
        data = data[1:]
    if len(data) != 0 and re.fullmatch(number_pattern, data):
        if re.fullmatch(integer_pattern, data):
            return sign * int(data)
        elif re.fullmatch(float_pattern, data) or re.fullmatch(std_pattern, data):
            return sign * float(data)
        elif re.fullmatch(hexadecimal_pattern, data):
            return int(data, base=16)
        elif re.fullmatch(binary_pattern, data):
            return int(data, base=2)
        elif re.fullmatch(octal_pattern, data):
            return int(data, base=8)
        else:
            raise Exception("parsing error")
    elif len(data) != 0 and params is not None and params.keys().__contains__(data):
        _data = params.get(data)
        if not node_return:
            if isinstance(_data, Node):
                return sign * params.get(data).data
            else:
                return sign * params.get(data)
        else:
            if sign == -1:
                return Node.init_root("neg_f", "0-" + _data.data, [])
            else:
                return _data
    elif len(data) != 0 and exec.data.get("const").keys().__contains__(data):
        return sign * exec.data.get("const").get(data)
    elif len(data) != 0 and exec.data.get("var").keys().__contains__(data):
        if not node_return:
            return sign * execute(exec.data.get("var").get(data))
        else:
            if sign == -1:
                return Node.init_root("neg_f", "0-" + data, [])
            else:
                return exec.data.get("var").get(data)
    elif len(data) != 0 and exec.data.get("lst").keys().__contains__(data):
        return exec.data.get("lst").get(data)
    elif len(data) != 0 and tp.temps.keys().__contains__(data):
        return tp.temps.get(data)
    if force_ex:
        raise Exception(data + " does not exist")
    else:
        return None


def swap_std_exp(data, params):
    """"parses standard expression"""
    new_data = data
    if re.search(std_enhanced_pattern, data):
        d_list = re.findall(std_enhanced_pattern, data)
        for d in d_list:
            p_list = [i for i, c in enumerate(d) if c == 'e']
            start = 0
            changed = False
            for s in p_list:
                try:
                    first = var_from_str(d[start:s], params)
                    second = var_from_str(d[s+1:], params)
                    replacement = "(" + str(first) + "*10**" + str(second) + ")"
                    new_data = data.replace(d, replacement)
                    changed = True
                except Exception:
                    start = s+1
            if not changed:
                return data
    return new_data


def count_nodes(func, data, params):
    count = 0
    for d in data:
        _d = var_from_str(d, params, False)
        if isinstance(_d, list) and not exec.list_funs.__contains__(func):
            count += len(_d)
        else:
            count += 1
    return count


def get_index(data):
    """"function returns index value of indexed list, everything are strings, no error checking"""
    data = str(data)
    o_br = [i for i, v in enumerate(data) if v == '[']
    c_br = [i for i, v in enumerate(data) if v == ']']
    return data[o_br[0] + 1:c_br[-1]]


def parse_pluses_minuses(data):
    """"function removes unnecessary pluses and minuses"""
    new_data = []
    for i, c in enumerate(data):
        if c == '+' and (len(new_data) == 0 or re.match(operators, new_data[-1])):
            continue
        elif c == '-':
            if i == 0:
                new_data.append('0')
                new_data.append('-')
            elif new_data[-1] == '-':
                new_data[-1] = '+'
            elif new_data[-1] == '+':
                new_data[-1] = '-'
            else:
                new_data.append('-')
        else:
            new_data.append(c)
    new_data_string = "".join(new_data)
    return new_data_string
