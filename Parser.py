import re
from ast import literal_eval
import exec
import function as f


# command_pattern = re.compile(r"^[a-zA-Z0-9_\s]+(\s+[a-zA-Z0-9_-]+\s*)*$")
func_pattern = re.compile(r"^([\w\d()+*\-/.,^=%!|&\"_]+)\s*$")
command_pattern = re.compile(r"^[\w\d_\s]+(\s+[\w\d()+*\-/.,^%!=|&\"_]+\s*)*$")
assignment_pattern = re.compile(r"^[\w\d\s_]+:\s?[\w\d()+*\-/.,^%!|&\"_]+\s*$")
exec_pattern = re.compile(r"^([\w\d_]+(\([\w\d\s_]+\)))+|([\w\d()+*\-/.,^=%!|&\"_]+)\s*$")
udf_pattern = re.compile(r"^([\w\d_]+(\([\w\d\s_]+\)))\s*$")
number_pattern = re.compile(r"(^(0[bB])[01]+$)|(^(0[oO])[0-7]+$)|(^(0[xX])[0-9a-fA-F]+$)|(^[-+]?[0-9]*$)|(^[-+]?"
                            r"[0-9]*\.[0-9]+$)|(^[-+]?[0-9]*\.?[0-9]+e[-+]?[0-9]+$)")
kwargs_patter = re.compile(r"[\w\d_]+=[\w\d_]+")


def parse(line):
    try:
        if re.match(command_pattern, line) and not re.fullmatch(number_pattern, line) and \
                not exec.constants.keys().__contains__(line) and not exec.vars.keys().__contains__(line):
            parts = re.split(r"[\s]+", line)
            com = parts[0]
            args, kwargs = format_inputs(parts[1:])
            if not exec.built_ins.keys().__contains__(com):
                print("no such command")
                return
            else:
                exec.built_ins.get(com)(*args, **kwargs)
        elif re.match(assignment_pattern, line):
            parts = re.split(r"[\s]+", line.replace(":", " "))
            if len(parts) == 2 and (re.match(number_pattern, parts[1]) or re.match(exec_pattern, parts[1])):
                exec.addv(*parts)
            elif len(parts) >= 3 and re.match(func_pattern, parts[-1]):
                exec.addf(*parts)
        elif re.fullmatch(exec_pattern, line):
            if re.fullmatch(number_pattern, line):
                result = f.var_from_str(line)
            else:
                result = f.var_from_str(line, force_ex=False)
                if result is None:
                    function = f.Node.init_root("temp", line, [])
                    result = f.execute(function)
            print(result)
        else:
            print("syntax error")
    except Exception as e:
        print(str(e))


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

