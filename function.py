import exec
import re
# from sys import maxsize

number_pattern = re.compile(r"(^(0[bB])[01]+$)|(^(0[oO])[0-7]+$)|(^(0[xX])[0-9a-fA-F]+$)|(^[-+]?[0-9]*$)|(^[-+]?"
                            r"[0-9]*\.[0-9]+$)|(^[-+]?[0-9]*\.?[0-9]+e[-+]?[0-9]+$)")
binary_pattern = re.compile(r"(^(0[bB])[01]+$)")
octal_pattern = re.compile(r"(^(0[oO])[0-7]+$)")
hexadecimal_pattern = re.compile(r"(^(0[xX])[0-9a-fA-F]+$)")
integer_pattern = re.compile(r"(^[-+]?[0-9]*$)")
float_pattern = re.compile(r"(^[-+]?[0-9]*\.[0-9]+$)")
std_pattern = re.compile(r"(^[-+]?[0-9]*\.?[0-9]+e[-]?[0-9]+$)")
std_enhanced_pattern = re.compile(r"([-]?[\w\d_.#]+e[-]?[\w\d_.#]+)")
levels = [r"\+", r"[\w\d_]-", r"[^*](\*)[^*]", r"\/", r"(?:\*\*)", r"[\d\w_]+#"]
level_str = ["+", "-", "*", "/", "**", ""]
basic_multi = re.compile(r"-?[\w\d_.,]+")
basic = re.compile(r"-?[\w\d_.]+")
func_pattern = re.compile(r"[\d\w_]*#")


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
    def init_root(cls, name, data, params):
        """"__init__for root node"""
        root = Node()
        root.name = name
        for i in params:
            root.parameters.update({i: i})
        # data = swap_std_exp(data)
        root.data_as_str = str(data)
        init_tree(root, data, 0, root.parameters)
        for p in params:
            # if not root.__contains__(p):
            if not re.search(r"(?:^|[(,+\-*|/])" + p + r"(?:$|[),+\-*|/])", root.data_as_str):
                raise Exception(f"there is no \"{p}\" in function: {data}")
        return root

    def __str__(self):
        return f"{self.name}{list(self.parameters.keys())}: {self.data_as_str}"

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
            for k, v in zip(self.data.parameters.keys(), args):
                d.update({k: iterate(v, {})})
            return iterate(self.data, d)
        else:
            return iterate(self, d)


def iterate(root, params):
    """"one iteration of recursive function execution"""
    if isinstance(root, Node) and isinstance(root.data, Node) and exec.u_funs.get(root.data.name) is not None:
        return root(*root.nodes)
    if len(root.nodes) != 0:
        l = []
        for n in root.nodes:
            l.append(iterate(n, params))
        return root.data(*l)
    elif params.keys().__contains__(str(root.data)):
        return params.get(str(root.data))
    else:
        return root.data


def init_tree(root, data, level, params):
    """"creates inner function"""
    leftover, funcs = strip_functions(data)
    leftover = swap_std_exp(leftover, params)
    return pass_levels(root, leftover, funcs, level, params)


def pass_levels(parent, data, inner, level, params):
    """"creates new node for function(recursive) separated by operators"""
    inner_taken = 0
    strings, func, tree = get_level(data, level)
    if func is not None:
        max_nodes = func[1]
        parent.data = func[0]
        if tree:
            f_data, f_list = strip_functions(inner[0])
            f_data = re.split(r",", f_data)
            funs = dress_up_functions(f_data, f_list)
            for i in range(len(funs)):
                if re.fullmatch(basic_multi, funs[i]):
                    add_single(parent, funs[i], params)
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
                # if re.match(r"[\w]+#", string):
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
                    parent.nodes.append(
                        pass_levels(Node(params=params, name=string), string, inner[inner_taken - inner_count: inner_taken], level, params))
            else:
                raise Exception("out of nodes")
        return parent
    else:
        parent.nodes.append(init_tree(Node(params=params, name=inner[0]), inner[0], 0, params))
        return parent


def params_to_list(parent, data):
    data.strip(',')
    par = re.split(r",", data)
    for p in par:
        parent.nodes.append(Node(var_from_str(p, par)))


def add_single(parent, data, params):
    """"adds comma separated non functional nodes to function tree"""
    data.strip(',')
    par = re.split(r",", data)
    for p in par:
        parent.nodes.append(Node(var_from_str(p, params), params=params))


def get_level(data, level):
    """"gets separator function, other stuff"""
    data = str(data)
    matcher = level_str[0]
    tree = False
    for l in range(level, len(levels)):
        if bool(re.search(levels[l], data)):
            level = l
            matcher = level_str[l]
            break
    fixed = []
    if level + 1 < len(levels):
        strings = data.split(matcher)
        if strings.__contains__(""):
            count = 0
            is_empty = False
            if matcher == "+":
                while strings.__contains__(""):
                    strings.remove("")
            elif matcher == "-":
                pre_fixed = []
                for i in range(len(strings)):
                    if strings[i] == "":
                        is_empty = True
                        count += 1
                    elif is_empty:
                        is_empty = False
                        if count % 2 == 0:
                            pre_fixed.append(strings[i])
                        else:
                            pre_fixed.append("-" + strings[i])
                        count = 0
                    else:
                        pre_fixed.append(strings[i])
                fixed = [pre_fixed[0]]
                index = 0
                pre_index = 2
                while pre_index < len(pre_fixed):
                    if re.match(r"[\w\d_]", fixed[index][-1]):
                        fixed.append(pre_fixed[pre_index])
                        index += 1
                    else:
                        fixed[index] = fixed[index] + "-" + pre_fixed[pre_index]
                    pre_index += 1
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
        func = exec.data.get("func").get(level_str[level])
    else:
        s = str(re.search(levels[level], data).group()).strip('#')
        if exec.data.get("func").keys().__contains__(s):
            func = exec.data.get("func").get(s)
        else:
            func = exec.data.get("udf").get(s)
        tree = True
    return fixed, func, tree


def strip_functions(data):
    """"strips function of brackets and replaces them with #"""
    fun_list = []
    l_indices = [i for i, ltr in enumerate(data) if ltr == '(']
    r_indices = [i for i, ltr in enumerate(data) if ltr == ')']
    if len(l_indices) != len(r_indices):
        raise Exception("wrong number of \"()\"")
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
                raise Exception("wrong order of brackets")
            if l_par_count < len(l_indices) and l_indices[l_index + 1] < r_indices[r_index]:
                l_index += 1
                l_par_count += 1
            elif r_par_count < len(r_indices):
                r_index += 1
                r_par_count += 1
                r_bound = r_indices[r_index]
        for s in fun_list:
            data = data.replace(s, '#')
        data = data.replace("|#|", "abs#")
        for s in fun_list:
            f_list.append(s[1: -1])
    return data, f_list


def dress_up_functions(h_string_arr, inner):
    """"opposite of 'strip_functions' but returns array of functions, if used with'strip_functions' can separate
    comma separated functions"""
    function_arr = []
    count = 0
    for f in h_string_arr:
        fun = ""
        for c in f:
            if c == '#':
                fun = fun + "(" + inner[count] + ")"
                count += 1
            else:
                fun = fun + c
        function_arr.append(fun)
    return function_arr


def var_from_str(data, params=None, force_ex=True):
    """"parses variable, constant-variable or non_decimal system number to number"""
    sign = 1
    if data[0] == '-':
        sign = -1
    if re.match(r"[+-]", data):
        data = data[1:]
    if re.fullmatch(number_pattern, data):
        if re.fullmatch(integer_pattern, data):
            return sign * int(data)
        elif re.fullmatch(float_pattern, data) or re.fullmatch(std_pattern, data):
            return sign * float(data)
        elif re.fullmatch(hexadecimal_pattern, data):
            return hex(data)
        elif re.fullmatch(binary_pattern, data):
            return bin(data)
        elif re.fullmatch(octal_pattern, data):
            return oct(data)
        else:
            raise Exception("parsing error")
    elif params is not None and params.keys().__contains__(data):
        return sign * params.get(data)
        # for p in params:
        #     if data == p:
        #         return sign * p
    elif exec.data.get("const").keys().__contains__(data):
        return sign * exec.data.get("const").get(data)
    elif exec.data.get("var").keys().__contains__(data):
        return sign * exec.data.get("var").get(data)
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
                    replacement = str(first) + "*10**" + str(second)
                    new_data = data.replace(d, replacement)
                    changed = True
                except Exception:
                    start = s+1
            if not changed:
                raise Exception("Syntax error in std expression")
    return new_data
