import re
import function as f
import temp_pool as tp
import Parser as P

exec_pattern = re.compile(r"^([\w\d_]+(\([\w\d\s_]+\))?)+|^([\w\d(){}@#$;+*\-.,<>^=%!|&\"_\]][\w\d(){}@;+*\-.,<>^=%!|&\"_\[\]]*)\s*$")
# enum_pattern = re.compile(r"\d[\d,]*")
# list_exec_pattern_no_sp = re.compile(r"^\[[\w()\[\]+*\-/.,^%!|&\"_]+\]\s*$")
list_comp_pattern = re.compile(r"^[\s#@]+$")
# basic_list_pattern = re.compile(r"^\[[\w,#@]+\]\s*$")
basic_list_pattern = re.compile(r"^\[[\w\s(){}#@$;\[\]+*\-/.,<>^%=!|&\"\'_]+\]\s*$")
number_pattern = re.compile(r"(^(0[bB])[01]+$)|(^(0[oO])[0-7]+$)|(^(0[xX])[0-9a-fA-F]+$)|(^[-+]?[0-9]*$)|(^[-+]?"
                            r"[0-9]*\.[0-9]+$)|(^[-+]?[0-9]*\.?[0-9]+e[-+]?[0-9]+$)")
list_exec_pattern = re.compile(r"^[/[][\w\s()@$#\[\]+*\-/.<>=,^%!|&\"_]+[\w\s()@$#\[\]+*\-/.<>=,^%!|&\"_]*(?:\sfor\s)[\w\s,_@#$]+(?:\sin\s)[\w\s()@$\[\]+*\-/.,<>=^%!|&\"_]+\]\s*$")
# list_exec_pattern = re.compile(r"^\[[\w\s()@$#\[\]+*\-/.,^%!|&\"_]+(?:\sfor\s)[\w\s,_@#$]+(?:\sin\s)[\w\s()@$\[\]+*\-/.,^%!|&\"_]+\]\s*$")
none_pattern = re.compile(r"([\s]+)|(^$)")
string_list_pattern = re.compile(r"\"[\w_]+\"\s*")
string_pattern = re.compile(r"\'[\w_]+\'\s*")
literal_pattern = re.compile(r"[\w_]")

in_pattern = re.compile(r"\s(?:in)\s")
for_pattern = re.compile(r"\s(?:for)\s")
if_pattern = re.compile(r"\s(?:if)\s")
else_pattern = re.compile(r"\s(?:else)\s")


def make_list_node(lst, data, const=False):
    """"converts regular data e.g. int,  float, to 'list' compatible Node """
    data = str(data)
    if re.fullmatch(number_pattern, data):
        result = f.nodefy(f.var_from_str(data, node_return=True))
        lst.append(result)
    elif re.fullmatch(string_list_pattern, data):
        for s in data.strip("\""):
            lst.append(f.nodefy(s))
    elif re.fullmatch(string_pattern, data):
        lst.append(f.nodefy(data.strip("\'")))
    else:
        result = f.nodefy(f.var_from_str(data, force_ex=False, node_return=True))
        if result is None:
            function = f.Node.init_root("temp", data, [])
            if const:
                result = f.nodefy(f.execute(function))
                lst.append(result)
            else:
                lst.append(function)
        else:
            if const:
                lst.append(f.nodefy(result.data))
            else:
                lst.append(result)


def make_list(data_string, cmds, const=False):
    """"parses simple and advanced list strings into lists"""
    data, f_list = separate_list_comp(data_string)
    if re.fullmatch(basic_list_pattern, "[" + data_string + "]") and not re.fullmatch(list_exec_pattern, "[" + data_string + "]"):
        f_data, f_list = f.strip_functions(data_string, "([", ")]", "#")
        f_data = re.split(r",", f_data)
        funs = f.dress_up_functions(f_data, f_list)
        res_list = []
        for cmd in cmds:
            P.parse(cmd)
        for p in funs:
            make_list_node(res_list, p, const=const)
        return res_list
    iter_list = []
    lvl1 = re.split(for_pattern, data)
    fr_half_et_count = lvl1[0].count("@")
    sc_half_et_count = lvl1[1].count("@")
    if sc_half_et_count != 0:
        for c in cmds[fr_half_et_count + 1: len(cmds)]:
            P.parse(c)
        lvl1[1] = lvl1[1].replace("@", "")
    if len(lvl1) != 2:
        raise Exception("missing for statement")
    lvl2_2 = re.split(in_pattern, lvl1[1])
    if len(lvl2_2) != 2:
        raise Exception("missing in statement")
    for_args = lvl2_2[0].replace(" ", "").split(",")
    for v in for_args:
        if f.var_from_str(v, force_ex=False) is not None:
            raise Exception("wrong argument name: " + v)
    h_count = 0
    _f_data, _f_list = f.strip_functions(lvl2_2[1], "([", ")]", "@")
    _f_data = [s.strip() for s in re.split(r",", _f_data)]
    funs = f.dress_up_functions(_f_data, _f_list, swap_char='@')
    for l in funs:
        if l == "#":
            iter_list.append(make_list(f_list[h_count], []))
            h_count += 1
        else:
            _l = f.var_from_str(l, force_ex=False)
            if _l is None:
                function = f.Node.init_root("temp", l, [])
                _l = f.execute(function)
            if isinstance(_l, list):
                iter_list.append(_l)
            else:
                raise Exception(str(_l) + " is not a list")
    lvl2_1 = re.split(if_pattern, lvl1[0])
    cmds_group = [[], [], []]
    c_count = 0
    if re.fullmatch(exec_pattern, lvl2_1[0]):
        _c_count = lvl2_1[0].count("@")
        lvl2_1[0] = lvl2_1[0].replace("@", "")
        cmds_group[1] = cmds[c_count: c_count+_c_count]
        c_count += _c_count
        if re.fullmatch(none_pattern, lvl2_1[0]):
            t0_name = None
        else:
            main_function = f.Node.init_root("temp", lvl2_1[0], for_args, superss=True)
            t0_name = tp.add_t(main_function, len(for_args))
        if len(lvl2_1) == 1:
            return lst_iterate_f(iter_list, for_args, t0_name, _cmds=cmds_group, const=const)
    else:
        raise Exception("list comp syntax error")
    if len(lvl2_1) > 2:
        raise Exception("too much if statements")
    lvl3 = re.split(else_pattern, lvl2_1[1])
    _c_count = lvl3[0].count("@")
    lvl3[0] = lvl3[0].replace("@", "")
    cmds_group[0] = cmds[c_count: c_count + _c_count]
    c_count += _c_count
    if_function = f.Node.init_root("temp", lvl3[0], for_args, superss=True)
    t1_name = tp.add_t(if_function, len(for_args))
    if len(lvl3) == 1:
        return lst_iterate_f(iter_list, for_args, t0_name, t1_name, _cmds=cmds_group, const=const)
    elif len(lvl3) == 2:
        _c_count = lvl3[0].count("@")
        lvl3[1] = lvl3[1].replace("@", "")
        cmds_group[2] = cmds[c_count: c_count + _c_count]
        c_count += _c_count
        else_function = f.Node.init_root("temp", lvl3[1], for_args, superss=True)
        t2_name = tp.add_t(else_function, len(for_args))
        return lst_iterate_f(iter_list, for_args, t0_name, t1_name, t2_name, _cmds=cmds_group, const=const)
    else:
        raise Exception("too much else statements")


def lst_iterate_f(lst, iter_args, main_func=None, if_func=None, secondary_func=None, _cmds=([], [], []), const=False):
    """executes advanced list (list_comp)"""
    min_length = float("inf")
    for l in lst:
        if len(l) < min_length:
            min_length = len(l)
    ans = []
    for i in range(min_length):
        cmds = []
        _ls = []
        for ls in lst:
            _ls.append(ls[i])
        for k in range(len(_cmds)):
            cmds.append(_cmds[k].copy())
            for j in range(len(cmds[k])):
                cs = cmds[k][j].split("$")
                csum = cs[0]
                for c_part in cs[1:len(cs)]:
                    found = False
                    for it in range(len(iter_args)):
                        try:
                            ind = c_part.index(iter_args[it])
                        except ValueError:
                            ind = -1
                        if ind == 0 and not re.fullmatch(literal_pattern, c_part[len(iter_args[it])]):
                            found = True
                            csum = csum + str(lst[it][i]) + str(c_part[len(iter_args[it]):])
                    if not found:
                        raise Exception("command variable not found")
                cmds[k][j] = csum
        ls_str = ",".join(iter_args)
        dict_args = {k: f.execute(v) for k, v in zip(iter_args, _ls)}
        for cmd in cmds[0]:
            P.parse(cmd)
        if if_func is None or bool(f.execute(f.Node.init_root("t", if_func + "(" + ls_str + ")", dict_args, superss=True))):
            for cmd in cmds[1]:
                P.parse(cmd)
            if main_func is not None:
                if const:
                    ans.append(f.nodefy(f.execute(f.Node.init_root("t", main_func + "(" + ls_str + ")", dict_args, superss=True))))
                else:
                    ans.append(f.Node.init_root("t", main_func + "(" + ls_str + ")", dict_args, superss=True))
        elif secondary_func is not None:
            for cmd in cmds[2]:
                P.parse(cmd)
            if const:
                ans.append(f.nodefy(f.execute(f.Node.init_root("t", secondary_func + "(" + ls_str + ")", dict_args, superss=True))))
            else:
                ans.append(f.Node.init_root("t", secondary_func + "(" + ls_str + ")", dict_args, superss=True))
    return ans


def separate_list_comp(data, clean=False):
    """"strips function of brackets and replaces them with #"""
    fun_list = []
    l_indices = [i for i, ltr in enumerate(data) if ltr == '[']
    r_indices = [i for i, ltr in enumerate(data) if ltr == ']']
    if len(l_indices) != len(r_indices):
        raise Exception("wrong number of \"[]\"")
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
            data = data.replace(s, '#', 1)
        if clean and not re.match(list_comp_pattern, data):
            raise Exception("list syntax error")
        for s in fun_list:
            f_list.append(s[1: -1])
    return data, f_list
