import sys
l = 1
r = 1e9
while(l <= r):
    md = int((l+r)//2)
    print(md)
    x = input()
    if(x == '='):
        print("! " + str(md))
        sys.stdout.flush()
        break;
    elif(x == '>'):
        l = md + 1
    else:
        r = md - 1




