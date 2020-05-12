
import Parser as p
import exec


exec.__collect_names()
print("pCal 1.0")
# line = input()

# p.parse(line)

while True:
    line = input()
    p.parse(line)