

temps = {}
count = 0


def add_t(func, arg_len):
    global temps
    global count
    name = "temp" + str(count)
    count += 1
    temps.update({name: (func, arg_len)})
    return name


def empty_tp():
    global temps
    global count
    count = 0
    temps = {}
