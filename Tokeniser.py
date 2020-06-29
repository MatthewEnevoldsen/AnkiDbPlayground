
def separatefirstword(str, dict):
    maxwordlen = 10
    for i in range(max(len(str) - maxwordlen, 1), len(str) - 1):
        if str[0:len(str) - i] in dict:
            return (str[0:len(str) - i], str[len(str) - i: len(str)])
    return None


def splittowords(str, dict):
    words = []
    left = str
    while len(left) > 0:
        res = separatefirstword(left, dict)
        if res is None:
            left = left[1:]
        else:
            word, left = res
            words.append(word)
    return words