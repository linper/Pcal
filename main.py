from sys import argv, exit
import Parser as p
# import readline
import exec


if __name__ == '__main__':
    exec.__collect_names()
    if len(argv) != 1:
        p.parse(" ".join(argv[1:len(argv)]), False)
        exit(0)
    else:
        print("PCal 1.0")
        while True:
            line = input()
            p.parse(line, False)
