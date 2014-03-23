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


def nreverse(lst):
    ret = kNil
    while lst['tag'] == 'cons':
        tmp = lst['cdr']
        lst['cdr'] = ret
        ret = lst
        lst = tmp
    return ret


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
        return readList(str[1:])
    elif str[0] == kQuote:
        elm, next = read(str[1:])
        return makeCons(makeSym('quote'), makeCons(elm, kNil)), next
    else:
        return readAtom(str)

def readList(str):
    ret = kNil
    while True:
        str = skipSpaces(str)
        if str == '':
            return makeError('unfinished parenthesis'), ''
        elif str[0] == kRPar:
            break
        elm, next = read(str)
        if elm['tag'] == 'error':
            return elm
        ret = makeCons(elm, ret)
        str = next
    return nreverse(ret), str[1:]

def printObj(obj):
    if obj['tag'] == 'num' or obj['tag'] == 'sym' or obj['tag'] == 'nil':
        return str(obj['data'])
    elif obj['tag'] == 'error':
        return '<error: %s>' % obj['data']
    elif obj['tag'] == 'cons':
        return printList(obj)
    elif obj['tag'] == 'subr':
        return '<subr>'
    elif obj['tag'] == 'expr':
        return '<expr>'

def printList(obj):
    ret = ''
    first = True
    while obj['tag'] == 'cons':
        if first:
            ret = printObj(obj['car'])
            first = False
        else:
            ret += ' ' + printObj(obj['car'])
        obj = obj['cdr']
    if obj['tag'] == 'nil':
        return '(%s)' % ret
    return '(%s . %s)' % (ret, printObj(obj))

def findVar(sym, env):
    while env['tag'] == 'cons':
        alist = env['car']
        while alist['tag'] == 'cons':
            if alist['car']['car'] == sym:
                return alist['car']
            alist = alist['cdr']
        env = env['cdr']
    return kNil

g_env = makeCons(kNil, kNil)

def addToEnv(sym, val, env):
    env['car'] = makeCons(makeCons(sym, val), env['car'])


def eval1(obj, env):
    if obj['tag'] == 'nil' or obj['tag'] == 'num' or obj['tag'] == 'error':
        return obj
    elif obj['tag'] == 'sym':
        bind = findVar(obj, env)
        if bind == kNil:
            return makeError('%s has no value' % obj['data'])
        return bind['cdr']
    return makeError('noimpl')

addToEnv(makeSym('t'), makeSym('t'), g_env)

while True:
    try:
        exp, _ = read(raw_input())
        print printObj(eval1(exp, g_env))
    except (EOFError):
        break
