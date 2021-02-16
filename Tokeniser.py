from typing import List, Tuple


def separatelastword(str, dict):
    maxwordlen = 10
    for i in range(min(len(str), maxwordlen), 0, -1):
        if str[-i:] in dict:
            return (str[-i:], str[0:-i])
    return None


def splittowords(str, dict):
    words = []
    right = str
    while len(right) > 0:
        res = separatelastword(right, dict)
        if res is None:
            right = right[0:-1]
        else:
            word, right = res
            words.append(word)
    words.reverse()
    return words

def allfirstwords(str, dict):
    maxwordlen = 10
    return [str[0:i] for i in range(min(len(str), maxwordlen), 0, -1) if str[0:i] in dict]
def recyboy(str, dict) -> List[List[str]]:
    words = allfirstwords(str, dict)
    if not any(str):
        return [[]]
    if not any(words):
        return recyboy(str[1:], dict)
    for w in words:
        return [[w] + res for res in recyboy(str[len(w):], dict)]
def maxlensqtokens(str, dict):
    def sumsqlen(strs):
        return sum([len(s) * len(s) for s in strs])
    best: List[str] = []
    poss = recyboy(str, dict)
    for p in poss:
        if sumsqlen(p) > sumsqlen(best):
            best = p
    return best






