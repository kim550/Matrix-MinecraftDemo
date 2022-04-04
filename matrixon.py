from settings import Settings

class MatrixonParser:
    def __init__(self):
        self.globals = {}

    def parse_decorator(self, decorator):
        name = decorator.split(' ')[0]
        if name == 'raw':
            code = decorator[4:]
            exec(code)

    def run(self, line):
        if line.startswith('#'):
            self.parse_decorator(line[1:])

mparser = MatrixonParser()

def expression(expr):
    if expr.isdigit():
        return int(expr)
    else:
        try:
            return float(expr)
        except ValueError:
            pass

def exec_matrixon(data):
    code = ' '.join(data[1:])
    codes = code.split('$')
    for line in codes:
        line.replace('\\$', '$')
        mparser.run(line)

def exec_gamemode(data):
    if expression(data[1]) in [1, 2]:
        gamemode = expression(data[1])
        Settings.gamemode = gamemode

def exec_tp(data):
    if type(expression(data[1])) in (int, float) and type(expression(data[2])) in (int, float) and type(expression(data[3])) in (int, float):
        Settings.window.position = expression(data[1]), expression(data[2]), expression(data[3])

commands = {'/matrixon': exec_matrixon, '/gamemode': exec_gamemode, '/tp': exec_tp}

def run(script):
    data = script.split(' ')
    commands[data[0]](data)
