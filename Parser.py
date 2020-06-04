import re
from ast import literal_eval
import exec
import function as f
import temp_pool as tp
import lst


# command_pattern = re.compile(r"^[a-zA-Z0-9_\s]+(\s+[a-zA-Z0-9_-]+\s*)*$")
func_pattern = re.compile(r"^([\w\d(){};@+*\-/.,<>^=%!|&\"_]+)\s*$")
command_pattern = re.compile(r"^[\w\d_\s]+(\s+[\w\d(){};@+\[\]*\-/.,<>^%!=|&\"_]+\s*)*$")
# assignment_pattern = re.compile(r"^[\w\d\s_]+:\s?([\w\d()+*\-/.,^%!|&\"_])|(\[[\w\d()+*\-/.,^%!|&\"_]\])+\s*$")
assignment_pattern = re.compile(r"^[\w\s_]+:\s?(([\w\s(){};@\[\]+*\-/.,^=%!|&\"_]+)|(\[[\w\s(){}@;\[\]+*\-/.,<>^%=!|&\"_]+\]))\s*$")
list_assignment_pattern = re.compile(r"^[\w\s_]+:\s?\[[\w\s(){}@;\[\]+*\-/.,<>^%=!|&\"_]+\]\s*$")
# list_assignment_pattern = re.compile(r"^[\w\s_]+:\s?\[[\w\s()\[\]+*\-/.,^%!|&\"_]+(?:\sfor\s)[\w\s,_]+(?:\sin\s)[\w\s()\[\]+*\-/.,^%!|&\"_]+\]\s*$")
list_exec_pattern = re.compile(r"^\[[\w\s(){}@;\[\]+*\-/.,<>^%=!|&\"_]+\]\s*$")
# list_exec_pattern = re.compile(r"^\[[\w\s()\[\]+*\-/.,^%!|&\"_]+(?:\sfor\s)[\w\s,_]+(?:\sin\s)[\w\s()\[\]+*\-/.,^%!|&\"_]+\]\s*$")
exec_pattern = re.compile(r"^([\w\d_]+(\([\w\d\s_]+\))?)+|^([^\[][\w\d(){}@;+*\-.,<>^=%!|&\"_\[\]]+)\s*$")
# exec_pattern = re.compile(r"^([\w\d_]+(\([\w\d\s_]+\)))+|([\w\d()+*\-/.,<>^=%!|&\"_]+)\s*$")
# udf_pattern = re.compile(r"^([\w\d_]+(\([\w\d\s_]+\)))\s*$")
number_pattern = re.compile(r"(^(0[bB])[01]+$)|(^(0[oO])[0-7]+$)|(^(0[xX])[0-9a-fA-F]+$)|(^[-+]?[0-9]*$)|(^[-+]?"
                            r"[0-9]*\.[0-9]+$)|(^[-+]?[0-9]*\.?[0-9]+e[-+]?[0-9]+$)")
kwargs_patter = re.compile(r"[\w\d_]+=[\w\d_]+")
illegal_pattern = re.compile(r"[#@]+")


def parse(line, inner=True):
    try:
        if re.match(illegal_pattern, line):
            print("illegal characters: #,@")
            return
        orig, cmds = f.strip_functions(line, "{", "}", "@")
        h_count = 0
        for ln in orig.split(";"):
            ln = ln.strip()
            loc_h_count = ln.count("@")
            loc_cmds = cmds[h_count: h_count + loc_h_count]
            h_count += loc_h_count

            if re.match(command_pattern, ln) and not re.fullmatch(number_pattern, ln) and \
                    not exec.constants.keys().__contains__(ln) and not exec.vars.keys().__contains__(ln) and \
                    not exec.lsts.keys().__contains__(ln):
                parts = re.split(r"[\s]+", ln)
                com = parts[0]
                args, kwargs = format_inputs(parts[1:])
                if exec.cmd_func.__contains__(com):
                    args.append(loc_cmds)
                else:
                    for cmd in loc_cmds:
                        parse(cmd)
                if not exec.commands.keys().__contains__(com):
                    print("no such command")
                    return
                else:
                    exec.commands.get(com)(*args, **kwargs)
            elif re.match(assignment_pattern, ln) and not inner:
                parts = re.split(r"[\s]+", ln.replace(":", " "))
                if re.match(list_assignment_pattern, ln):
                    _, list_comps = lst.separate_list_comp(' '.join(parts[1: len(parts)]), clean=True)
                    lst_var = lst.make_list(list_comps[0], loc_cmds)
                    exec.addl(parts[0], lst_var, loc_cmds)
                else:
                    for cmd in loc_cmds:
                        parse(cmd)
                    if len(parts) == 2 and (re.match(number_pattern, parts[1]) or re.match(exec_pattern, parts[1])):
                        exec.addv(*parts)
                    elif len(parts) >= 3 and re.match(func_pattern, parts[-1]):
                        exec.addf(*parts)
                    else:
                        print("assignment failed")
            elif re.fullmatch(exec_pattern, ln) and not inner:
                for cmd in loc_cmds:
                    parse(cmd)
                if re.fullmatch(number_pattern, ln):
                    result = f.var_from_str(ln)
                else:
                    result = f.var_from_str(ln, force_ex=False)
                    if result is None:
                        function = f.Node.init_root("temp", ln, [])
                        result = f.execute(function)
                print(result)
            elif re.fullmatch(list_exec_pattern, ln) and not inner:
                result = lst.make_list(lst.separate_list_comp(ln, clean=True)[1][0], loc_cmds)
                print(result)
            else:
                print("syntax error")
    except Exception as e:
        print(str(e))
    finally:
        if not inner:
            tp.empty_tp()


def get_udf_name(data):
    """"gets name of user defined function"""
    try:
        name = data[:data.index("(")]
        if exec.data.get("udf").keys().__contains__(name):
            return name
        else:
            return None
    except ValueError:
        return None


def format_inputs(inputs):
    """"formats inputs as *args and **kwargs"""
    arg_list = []
    kwarg_dict = {}
    for i in inputs:
        i = i.replace(" ", "")
        if re.fullmatch(kwargs_patter, i):
            pair = re.split(r"=", i)
            kwarg_dict.update({pair[0]: pair[1]})
        elif re.match(number_pattern, i):
            arg_list.append(literal_eval(i))
        else:
            arg_list.append(i)
    return arg_list, kwarg_dict

