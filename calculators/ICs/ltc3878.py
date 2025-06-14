from helpers import *

# battery
CELLS = 4

CELL_V_MIN = 3.2
CELL_V_MAX = 4.2

V_MIN = CELLS * CELL_V_MIN
V_MAX = CELLS * CELL_V_MAX

print(f'''Vmin {mformat(V_MIN, V)}
Vmax {mformat(V_MAX, V)}''')

# Module
# load
AMP_MAX = 15 # provided to module

POWER_MAX = AMP_MAX * V_MAX
POWER_MIN = AMP_MAX * V_MIN
print(f'''Power per module:
  Min: {mformat(POWER_MIN, P)}
  Max: {mformat(POWER_MAX, P)}''')

# TODO update with values from datasheet
# MOSFET RDS(ON)
RDS_ON = 0.0067

GATE_CAP = 8e-9

# MOSFET temperature coefficients
P_T_TOP = 1.3
P_T_BOT = 1.3
FET_PT = 1.3 # remove 2 above

# Switching parameters (typical values, update these with actual MOSFET specs)
C_MILLER = 15e-9  # Miller capacitance
DR_TG_HIGH = 2.5  # gate driver pull-up resistance
DR_TG_LOW = 1.0   # gate driver pull-down resistance
V_MILLER = 2.5    # Miller effect threshold

print('LTC3878 buck converter')
V_OUT = 12

# assumptions
RMS_EFFICIENCY = 0.85
OUT_P_MAX = POWER_MAX * RMS_EFFICIENCY
OUT_P_MIN = POWER_MIN * RMS_EFFICIENCY
AMP_OUT_MAX = OUT_P_MAX / V_OUT
AMP_OUT_MIN = OUT_P_MIN / V_OUT
print(f"""
At efficiency {RMS_EFFICIENCY * 100}% and input current {AMP_MAX}A
 Output:
   Power MIN: {mf(OUT_P_MIN, P)}
   Power MAX: {mf(OUT_P_MAX, P)}
   Out current: MIN: {mf(AMP_OUT_MIN, A)}; MAX: {mf(AMP_OUT_MAX, A)}
""")

# from datasheet
V_INTVCC = 5.3
PT = 1.3 # temperature normalization factor; 1 at 25C; 1.3 at 100C; 1.5 at 125C
T_OFF_MIN = 220e-9 # s shortest time to turn of bot mos, trip current cmp, turn off bot
SENSE_V_MIN = 0.0266
SENSE_V_MAX = 0.266
SS_RATE = 1.3e6  # s/F (converted from s/µF)

# choices
FREQ = 200e3                                    # still need to research it, but higher freq -> more loses, but less space
R_CURRENT_P = 0.3                               # ripple current %
R_CURRENT = R_CURRENT_P * AMP_OUT_MAX           # ripple current
R_V_P = .01                                     # ripple voltage %
R_V = V_OUT * R_V_P                             # ripple voltage
AMP_LIMIT_P = 1.2                               # overcurrent %
AMP_LIMIT_TARGET = AMP_OUT_MAX * AMP_LIMIT_P    # overcurrent threshold
SS = 15e-3                                      # soft start time
print(f'''Chosen:
  Vout: {V_OUT}V
  Frequency: {mformat(FREQ, F)}
  Max ripple current: {R_CURRENT_P * 100}% aka {mformat(R_CURRENT, 'A')}
  Max ripple voltage: {R_V_P * 100}% aka {mformat(R_V, V)}
  Current limit: {AMP_LIMIT_P}% aka {mf(AMP_LIMIT_TARGET, A)}
''')

print("Stats")

# fet rds range
Rds_min = SENSE_V_MIN / ( AMP_OUT_MAX * PT )
Rds_max = SENSE_V_MAX / ( AMP_OUT_MAX * PT )

# duty cycles
D_TOP_MIN = V_OUT / V_MAX
D_TOP_MAX = V_OUT / V_MIN

D_BOT_MIN = 1 - V_OUT / V_MIN
D_BOT_MAX = 1 - V_OUT / V_MAX

# power dissipation
TOP_MAX_POWER = (D_TOP_MAX * (AMP_OUT_MAX**2) * P_T_TOP * RDS_ON +
                V_MAX**2 * (AMP_OUT_MAX / 2) * C_MILLER *
                ((DR_TG_HIGH / (V_INTVCC - V_MILLER)) + (DR_TG_LOW / V_MILLER)) * FREQ)

# Bottom FET power (conduction losses only - no switching in valley current mode)
BOT_MAX_POWER = D_BOT_MAX * (AMP_OUT_MAX**2) * P_T_BOT * RDS_ON

FREQ_MAX = 1 / ( V_OUT / (V_MIN * FREQ) + T_OFF_MIN )

print(f"""
Rds at pt = {PT}
  At min SenseV {mf(Rds_min, R)}
  At max SenseV {mf(Rds_max, R)}

Duty Cycles:
  Top FET:
    Min: {D_TOP_MIN * 100:.2f}%
    Max: {D_TOP_MAX * 100:.2f}%
  Bop FET:
    Min: {D_BOT_MIN * 100:.2f}%
    Max: {D_BOT_MAX * 100:.2f}%

Max freq to avoid dropout: {mf(FREQ_MAX, F)}

Power Dissipation:
    Top FET max: {mf(TOP_MAX_POWER, P)}
    Bot FET max: {mf(BOT_MAX_POWER, P)}
""")

print("Peripherals calcualtion")
# frequency setter
R_ON = V_OUT / (.7 * FREQ * 10e-12)
R_ON2 = ((V_INTVCC - .7) / .7) * R_ON

# must be bypassed to ground with a minimum of 1µF low ESR
# capacitance greater than 10µF is discouraged
C_INTV = 1e-6

# needs to store approximately 100 times the gate charge required
# by the top MOSFET. In most applications 0.1µF to 0.47µF,
# X5R or X7R dielectric capacitor is adequate.
# It is recommended that the BOOST capacitor be no larger
# than 10% of the INTVCC
C_BOOST = GATE_CAP * 100

C_SS = SS / SS_RATE

C_OUT_M = 2
C_OUT_esr = 5e-3
C_OUT = C_OUT_M * 1 / (8 * FREQ * (R_V / R_CURRENT - C_OUT_esr))
L_OUT_M = 1.5
L_OUT = L_OUT_M * (V_OUT - V_OUT**2 / V_MIN) / (FREQ * R_CURRENT)

# from ti info
C_IN_M = 2
C_IN_DC = V_OUT / (V_MAX * RMS_EFFICIENCY)
C_IN = C_IN_M * (AMP_OUT_MAX * C_IN_DC * (1-C_IN_DC) * 1000) / (FREQ/1e3 * 75*1e-3) * 1e-6
C_IN_RMS = AMP_OUT_MAX / 2

# Out voltage setter
R_A = 10e3 # connected to ground
R_B = (V_OUT / 0.8 - 1) * R_A
# from ti info
R_B_C = 1 / (2 * math.pi * FREQ) * math.sqrt(1/R_B * (1/R_B + 1/R_A))

# Vsns
V_SNS = RDS_ON * FET_PT * (AMP_LIMIT_TARGET - R_CURRENT / 2)
assert SENSE_V_MIN <= V_SNS <= SENSE_V_MAX, "Vsns out of range"
V_RNG = 7.5 * V_SNS
V_RNG_R2 = 10e3
V_RNG_R1 = V_RNG_R2 * (V_INTVCC - V_RNG) / V_RNG

print(f'''
To set frequency {mf(FREQ, F)};
    Ron = {mf(R_ON, R)}
    Ron2 = {mf(R_ON2, R)}
For Vout = {V_OUT}V:
    Ra: {mf(R_A, R)};
    Rb: {mf(R_B, R)}; FFC: {mf(R_B_C, C)}
For out current limit {mf(AMP_LIMIT_TARGET, A)}
    Vsns: {mf(V_SNS, V)}; to set it:
        Vrng voltage: {mf(V_RNG, V)}
            Divider from INTV: R1: {mf(V_RNG_R1, R)}; R2: {mf(V_RNG_R2, R)}
Fos soft-start of {SS*1e3}ms
    Capacitors: {mf(C_SS, C)}
Output inductor {mf(L_OUT, I)} for {R_CURRENT_P}% ripple current {mf(R_CURRENT, A)}
Input cap {mf(C_IN, C)}; RMS: {mf(C_IN_RMS, A)}
Output cap {mf(C_OUT, C)}; ESR {mf(C_OUT_esr, R)} for {R_V_P}% ripple voltage: {mf(R_V, V)}
INTV cap {mf(C_INTV, C)}
Boost cap {mf(C_BOOST, C)}; INTV_Cap ratio should be lower x10: {C_BOOST/C_INTV:.2f}
''')

T_ON_MIN = 0.7 / ((V_MIN - .7) / R_ON) * 10e-12
T_ON_MAX = 0.7 / ((V_MAX - .7) / R_ON) * 10e-12

V_IN_DROPOUT_THR = V_OUT * (T_ON_MAX + T_OFF_MIN ) / T_ON_MAX

print(f'''
Top mosfet on-time:
  Min voltage: {mf(T_ON_MIN, S)}
  Max voltage: {mf(T_ON_MAX, S)}
  Minimum possible Vin to avoid dropout: {mf(V_IN_DROPOUT_THR, V)}
''')