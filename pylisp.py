import re
import sys

# Change recursionlimit if you need more stack.
sys.setrecursionlimit(10000)

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

sym_t = makeSym('t')
sym_quote = makeSym('quote')
sym_if = makeSym('if')
sym_lambda = makeSym('lambda')
sym_defun = makeSym('defun')
sym_setq = makeSym('setq')
sym_loop = makeSym('loop')
sym_return = makeSym('return')
loop_val = kNil

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

def pairlis(lst1, lst2):
    ret = kNil
    while lst1['tag'] == 'cons' and lst2['tag'] == 'cons':
        ret = makeCons(makeCons(lst1['car'], lst2['car']), ret)
        lst1 = lst1['cdr']
        lst2 = lst2['cdr']
    return nreverse(ret)


def isDelimiter(c):
    return c == kLPar or c == kRPar or c == kQuote or c.isspace()

def skipSpaces(str):
    return re.sub('^\s+', '', str)

def makeNumOrSym(str):
    try:
        return makeNum(int(str))
    except:
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
        return makeCons(sym_quote, makeCons(elm, kNil)), next
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
            return elm, next
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
            first = False
        else:
            ret += ' '
        ret = printObj(obj['car'])
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

    op = safeCar(obj)
    args = safeCdr(obj)
    if op == sym_quote:
        return safeCar(args)
    elif op == sym_if:
        c = eval1(safeCar(args), env)
        if c['tag'] == 'error':
            return c
        elif c == kNil:
            return eval1(safeCar(safeCdr(safeCdr(args))), env)
        return eval1(safeCar(safeCdr(args)), env)
    elif op == sym_lambda:
        return makeExpr(args, env)
    elif op == sym_defun:
        expr = makeExpr(safeCdr(args), env)
        sym = safeCar(args)
        addToEnv(sym, expr, g_env)
        return sym
    elif op == sym_setq:
        val = eval1(safeCar(safeCdr(args)), env)
        if val['tag'] == 'error':
            return val
        sym = safeCar(args)
        bind = findVar(sym, env)
        if bind == kNil:
            addToEnv(sym, val, g_env)
        else:
            bind['cdr'] = val
        return val
    elif op == sym_loop:
        return loop(args, env)
    elif op == sym_return:
        global loop_val
        loop_val = eval1(safeCar(args), env)
        return makeError('')
    return apply(eval1(op, env), evlis(args, env), env)

def evlis(lst, env):
    ret = kNil
    while lst['tag'] == 'cons':
        elm = eval1(lst['car'], env)
        if elm['tag'] == 'error':
            return elm
        ret = makeCons(elm, ret)
        lst = lst['cdr']
    return nreverse(ret)

def progn(body, env):
    ret = kNil
    while body['tag'] == 'cons':
        ret = eval1(body['car'], env)
        if ret['tag'] == 'error':
            return ret
        body = body['cdr']
    return ret

def loop(body, env):
    while True:
        ret = progn(body, env)
        if ret['tag'] == 'error':
            if ret['data'] == '':
                return loop_val
            return ret

def apply(fn, args, env):
    if fn['tag'] == 'error':
        return fn
    elif args['tag'] == 'error':
        return args
    elif fn['tag'] == 'subr':
        return fn['data'](args)
    elif fn['tag'] == 'expr':
        return progn(fn['body'],
                     makeCons(pairlis(fn['args'], args), fn['env']))
    return makeError('noimpl')


def subrCar(args):
    return safeCar(safeCar(args))

def subrCdr(args):
    return safeCdr(safeCar(args))

def subrCons(args):
    return makeCons(safeCar(args), safeCar(safeCdr(args)))

def subrEq(args):
    x = safeCar(args)
    y = safeCar(safeCdr(args))
    if x['tag'] == 'num' and y['tag'] == 'num':
        if x['data'] == y['data']:
            return sym_t
        return kNil
    elif x is y:
        return sym_t
    return kNil

def subrAtom(args):
    if safeCar(args)['tag'] == 'cons':
        return kNil
    return sym_t

def subrNumberp(args):
    if safeCar(args)['tag'] == 'num':
        return sym_t
    return kNil

def subrSymbolp(args):
    if safeCar(args)['tag'] == 'sym':
        return sym_t
    return kNil

def subrAddOrMul(fn, init_val):
    def doit(args):
        ret = init_val
        while args['tag'] == 'cons':
            if args['car']['tag'] != 'num':
                return makeError('wrong type')
            ret = fn(ret, args['car']['data'])
            args = args['cdr']
        return makeNum(ret)
    return doit
subrAdd = subrAddOrMul(lambda x, y: x + y, 0)
subrMul = subrAddOrMul(lambda x, y: x * y, 1)

def subrSubOrDivOrMod(fn):
    def doit(args):
        x = safeCar(args)
        y = safeCar(safeCdr(args))
        if x['tag'] != 'num' or y['tag'] != 'num':
            return makeError('wrong type')
        return makeNum(fn(x['data'], y['data']))
    return doit
subrSub = subrSubOrDivOrMod(lambda x, y: x - y)
subrDiv = subrSubOrDivOrMod(lambda x, y: x / y)
subrMod = subrSubOrDivOrMod(lambda x, y: x % y)


addToEnv(makeSym('car'), makeSubr(subrCar), g_env)
addToEnv(makeSym('cdr'), makeSubr(subrCdr), g_env)
addToEnv(makeSym('cons'), makeSubr(subrCons), g_env)
addToEnv(makeSym('eq'), makeSubr(subrEq), g_env)
addToEnv(makeSym('atom'), makeSubr(subrAtom), g_env)
addToEnv(makeSym('numberp'), makeSubr(subrNumberp), g_env)
addToEnv(makeSym('symbolp'), makeSubr(subrSymbolp), g_env)
addToEnv(makeSym('+'), makeSubr(subrAdd), g_env)
addToEnv(makeSym('*'), makeSubr(subrMul), g_env)
addToEnv(makeSym('-'), makeSubr(subrSub), g_env)
addToEnv(makeSym('/'), makeSubr(subrDiv), g_env)
addToEnv(makeSym('mod'), makeSubr(subrMod), g_env)
addToEnv(sym_t, sym_t, g_env)

while True:
    try:
        print '>',
        exp, _ = read(raw_input())
        print printObj(eval1(exp, g_env))
    except (EOFError):
        break
