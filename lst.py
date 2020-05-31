import re
import exec
import function as f
import temp_pool as tp

exec_pattern = re.compile(r"^([\w\d_]+(\([\w\d\s_]+\)))+|([\w\d()+*\-/.,^=%!|&\"_]+)\s*$")
enum_pattern = re.compile(r"\d[\d,]*")
list_exec_pattern_no_sp = re.compile(r"^\[[\w()\[\]+*\-/.,^%!|&\"_]+\]\s*$")
list_comp_pattern = re.compile(r"^[\s#]+$")
basic_list_pattern = re.compile(r"^\[[\w,]+\]\s*$")
number_pattern = re.compile(r"(^(0[bB])[01]+$)|(^(0[oO])[0-7]+$)|(^(0[xX])[0-9a-fA-F]+$)|(^[-+]?[0-9]*$)|(^[-+]?"
                            r"[0-9]*\.[0-9]+$)|(^[-+]?[0-9]*\.?[0-9]+e[-+]?[0-9]+$)")
list_exec_pattern = re.compile(r"^\[[\w\s()\[\]+*\-/.,^%!|&\"_]+(?:\sfor\s)[\w\s,_]+(?:\sin\s)[\w\s()\[\]+*\-/.,^%!|&\"_]+\]\s*$")

in_pattern = re.compile(r"\s(?:in)\s")
for_pattern = re.compile(r"\s(?:for)\s")
if_pattern = re.compile(r"\s(?:if)\s")
else_pattern = re.compile(r"\s(?:else)\s")


def make_list(data_string):
    data, f_list = separate_list_comp(data_string)
    if re.fullmatch(basic_list_pattern, "[" + data_string + "]") and not re.fullmatch(list_exec_pattern, "[" + data_string + "]"):
        f_data, f_list = f.strip_functions(data_string)
        f_data = re.split(r",", f_data)
        funs = f.dress_up_functions(f_data, f_list)
        res_list = []
        for p in funs:
            if re.fullmatch(number_pattern, p):
                result = f.var_from_str(p)
            else:
                result = f.var_from_str(p, force_ex=False)
                if result is None:
                    function = f.Node.init_root("temp", p, [])
                    result = f.execute(function)
            res_list.append(result)
        return res_list
    iter_list = None
    if len(f_list) != 0:
        iter_list = make_list(f_list[0])
    lvl1 = re.split(for_pattern, data)

    if len(lvl1) != 2:
        raise Exception("missing for statement")
    lvl2_2 = re.split(in_pattern, lvl1[1])
    if len(lvl2_2) != 2:
        raise Exception("missing in statement")
    for_args = lvl2_2[0].replace(" ", "").split(",")
    for v in for_args:
        if f.var_from_str(v, force_ex=False) is not None:
            raise Exception("wrong argument name" + v)

    if iter_list is None or lvl2_2[1] != "#":
        if exec.data.get("lst").keys().__contains__(lvl2_2[1]):
            iter_list = f.var_from_str(lvl2_2[1], force_ex=True)
    lvl2_1 = re.split(if_pattern, lvl1[0])
    if re.fullmatch(exec_pattern, lvl2_1[0]):
        main_function = f.Node.init_root("temp", lvl2_1[0], for_args)
        t0_name = tp.add_t(main_function, len(for_args))
        if len(lvl2_1) == 1:
            return lst_iterate_f(iter_list, t0_name)
    else:
        raise Exception("list comp syntax error")
    if len(lvl2_1) > 2:
        raise Exception("too much if statements")
    lvl3 = re.split(else_pattern, lvl2_1[1])
    if_function = f.Node.init_root("temp", lvl3[0], for_args)
    t1_name = tp.add_t(if_function, len(for_args))
    if len(lvl3) == 1:
        return lst_iterate_f(iter_list, t0_name, t1_name)
    elif len(lvl3) == 2:
        else_function = f.Node.init_root("temp", lvl3[1], for_args)
        t2_name = tp.add_t(else_function, len(for_args))
        return lst_iterate_f(iter_list, t0_name, t1_name, t2_name)
    else:
        raise Exception("too much else statements")


def lst_iterate_f(lst, main_func, if_func=None, secondary_func=None):
    ans = []
    for v in lst:
        _f = f.Node.init_root("t", if_func + "(" + str(v) + ")", [])
        a = f.execute(_f)
        if if_func is None or bool(a):
            ans.append(f.execute(f.Node.init_root("t", main_func + "(" + str(v) + ")", [])))
        elif secondary_func is not None:
            ans.append(f.execute(f.Node.init_root("t", secondary_func + "(" + str(v) + ")", [])))
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
