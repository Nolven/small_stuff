import math

R = 'O' # resistor
V = 'V' # volt
F = 'H' # frequency
I = 'I' # inductor
P = 'W' # power
C = 'F' # capacitor
A = 'A' # amper
S = 'S' # seconds

# metric format
def mformat(value: float, unit: str, acc: int = 3) -> str:
    prefixes = [
        {"symbol": "a", "exp": -18},
        {"symbol": "f", "exp": -15},
        {"symbol": "p", "exp": -12},
        {"symbol": "n", "exp": -9},
        {"symbol": "μ", "exp": -6},
        {"symbol": "m", "exp": -3},
        {"symbol": "", "exp": 0},
        {"symbol": "k", "exp": 3},
        {"symbol": "M", "exp": 6},
        {"symbol": "G", "exp": 9},
        {"symbol": "T", "exp": 12},
        {"symbol": "P", "exp": 15},
        {"symbol": "E", "exp": 18}
    ]

    unit_formats = {
        R: 'Ω',     # Ohm
        V: 'V',     # Ohm
        F: 'Hz',    # Hertz
        I: 'H',     # Henry
        P: 'W',     # Watt
        C: 'F',     # Farad
        A: 'A',     # Farad
        S: 's',     # Farad
    }

    abs_value = abs(value)

    exponent = math.floor(math.log10(abs_value) / 3) * 3

    prefix = next((p for p in prefixes if p["exp"] == exponent), prefixes[6])
    display_value = value / (10 ** prefix["exp"])
    formatted_value = f"{display_value:.{acc}f}".rstrip('0').rstrip('.')

    return f"{formatted_value}{prefix['symbol']}{unit_formats.get(unit, unit)}"

mf = mformat