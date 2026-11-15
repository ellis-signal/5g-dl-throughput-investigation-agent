"""Shannon AWGN ideal capacity: domain validation and pure functions."""
import math

METHOD_VERSION = 'shannon-awgn-v1'
MODEL = 'Ideal single AWGN link (no interference/multiuser/overheads)'


def finite_number(value, name, *, positive=False, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f'{name}: expected a numeric value')
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f'{name}: must be finite')
    if positive and value <= 0:
        raise ValueError(f'{name}: must be > 0')
    if nonnegative and value < 0:
        raise ValueError(f'{name}: must be >= 0')
    return value


def calculate(bandwidth_mhz, snr_db):
    bandwidth_mhz = finite_number(bandwidth_mhz, 'bandwidth_mhz', positive=True)
    snr_db = finite_number(snr_db, 'snr_db')
    try:
        linear = 10.0 ** (snr_db / 10.0)
    except OverflowError as error:
        raise ValueError('snr_db: numeric overflow') from error
    if not math.isfinite(linear):
        raise ValueError('snr_db: numeric overflow')
    efficiency = math.log1p(linear) / math.log(2.0)
    capacity_mbps = bandwidth_mhz * efficiency
    if not math.isfinite(capacity_mbps) or capacity_mbps <= 0:
        raise ValueError('capacity: underflow/overflow for provided parameters')
    return {
        'bandwidth_mhz': bandwidth_mhz,
        'snr_db': snr_db,
        'snr_linear': linear,
        'spectral_efficiency_bps_hz': efficiency,
        'capacity_mbps': capacity_mbps,
        'method_version': METHOD_VERSION,
        'model': MODEL,
    }
