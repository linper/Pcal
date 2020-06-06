
import Parser as p
import readline
import exec

if __name__ == '__main__':
    exec.__collect_names()
    print("PCal 1.0")
    while True:
        line = input()
        p.parse(line, False)
