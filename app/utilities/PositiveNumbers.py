import bisect


class PositiveNumbers:
    Code = None
    MaxValue = None
    WkgSize = None
    EncodedLength = None

    def __init__(self, size=9, code=None):
        self.Code = [c for c in code or "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"]
        self.EncodedLength = size
        self.WkgSize = len(self.Code)
        self.MaxValue = int(self.WkgSize**self.EncodedLength)

    def encode(self, n):
        if n < 0 or n > self.MaxValue:
            return
        if n < self.WkgSize:
            return str(self.Code[int(n-self.WkgSize)]).rjust(self.EncodedLength, "0")
        else:
            def getchar(n, i):
                tmpn = n-self.WkgSize
                if i != self.EncodedLength:
                    tmpn = (tmpn/self.WkgSize**i)
                return self.Code[int(tmpn%self.WkgSize)]
            return "".join([getchar(n,i) for i in range(1, self.EncodedLength+1)])

    def decode(self, c):
        if len(c) == 1:
            return self.bisectSearchRC(self.Code, c)

        item_alt = 0
        if c[0] != "0":
            item_alt = self.WkgSize

        for i in range(1, self.EncodedLength+1):
            wkg_char = c[i-1:i]
            if wkg_char == "0":
                continue
            char = self.bisectSearchRC(self.Code, wkg_char)
            if i != self.EncodedLength:
                item_alt += char*(self.WkgSize**i)
            else:
                item_alt += char
        return item_alt

    def e(self, n):
        return self.encode(n)

    def d(self, n):
        return self.decode(n)

    def bisectSearchRC(self, haystack, item, index_pos=None, return_type=None):

        if not return_type:
            return_type = int

        def returnValue(value):
            if return_type is bool and value == -1:
                return False
            elif return_type is bool:
                return True
            elif value != -1:
                return value

        try:
            item_index = bisect.bisect_left(haystack, item)
            if item_index < len(haystack):
                if index_pos is not None and item[index_pos] == haystack[item_index][index_pos]:
                    return returnValue(item_index)
                elif index_pos is None and item == haystack[item_index]:
                    return returnValue(item_index)

        except Exception as inst:
            print("bisectSearchRC.ERROR", inst)

        return returnValue(-1)


# def run(v):
#    e = g.e(v)

#    d = g.d(e) if e else None
#    return (v == d)

# print(PositiveNumbers(123123123))
"""
run(1)
run(15)
run(60)
run(61)
run(62)
run(63)
run(1000)
run(12123)
run(12124)
run(12125)
run(25000)
run(88471)
run(5045902)
run(25760187211)
run(3142712836021)

print(PositiveNumbers(123123123))
"""
