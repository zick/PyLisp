import re

kLPar = '('
kRPar = ')'
kQuote = "'"
kNil = { 'tag': 'nil', 'data': 'nil' }

def safeCar(obj):
    if obj['tag'] == 'cons':
        return obj['car']
    return kNil

def safeCdr(obj):
    if obj['tag'] == 'cons':
        return obj['cdr']
    return kNil

def makeError(str):
    return { 'tag': 'error', 'data': str }

sym_table = {}
def makeSym(str):
    global sym_table
    if str == 'nil':
        return kNil
    if str not in sym_table:
        sym_table[str] = { 'tag': 'sym', 'data': str }
    return sym_table[str]

def makeNum(num):
    return { 'tag': 'num', 'data': num }

def makeCons(a, d):
    return { 'tag': 'cons', 'car': a, 'cdr': d }

def makeSubr(fn):
    return { 'tag': 'subr', 'data': fn }

def makeExpr(args, env):
    return { 'tag': 'expr',
             'args': safeCar(args),
             'body': safeCdr(args),
             'env': env }


def isDelimiter(c):
    return c == kLPar or c == kRPar or c == kQuote or c.isspace()

def skipSpaces(str):
    return re.sub('^\s+', '', str)

def makeNumOrSym(str):
  if re.search('^[+-]?\d+$', str):
      return makeNum(int(str))
  return makeSym(str)

def readAtom(str):
    next = ''
    for i in range(len(str)):
        if isDelimiter(str[i]):
            next = str[i:]
            str = str[:i]
            break
    return makeNumOrSym(str), next

def read(str):
    str = skipSpaces(str)
    if str == '':
        return makeError('empty input'), ''
    if str[0] == kRPar:
        return makeError('invalid syntax: %s' % str), ''
    elif str[0] == kLPar:
        return makeError('noimpl'), ''
    elif str[0] == kQuote:
        return makeError('noimpl'), ''
    else:
        return readAtom(str)

while True:
    try:
        print read(raw_input())
    except (EOFError):
        break
