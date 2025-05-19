import struct
import math



FCV_ENCODING_TYPES = {
    0x00: {
        "format": "4:4:4",
        "value_bytes": 4,
        "tangent_in_bytes": 4,
        "tangent_out_bytes": 4,
        "total_bytes": 12,
        "description": "Full float for value, in tangent, and out tangent (no compression)"
    },
    0x10: {
        "format": "4:2:2",
        "value_bytes": 4,
        "tangent_in_bytes": 2,
        "tangent_out_bytes": 2,
        "total_bytes": 8,
        "description": "Float value, 16-bit int tangents"
    },
    0x20: {
        "format": "4:1:1",
        "value_bytes": 4,
        "tangent_in_bytes": 1,
        "tangent_out_bytes": 1,
        "total_bytes": 6,
        "description": "Float value, 8-bit int tangents"
    },
    0x40: {
        "format": "2:4:4",
        "value_bytes": 2,
        "tangent_in_bytes": 4,
        "tangent_out_bytes": 4,
        "total_bytes": 10,
        "description": "16-bit value, float tangents"
    },
    0x50: {
        "format": "2:2:2",
        "value_bytes": 2,
        "tangent_in_bytes": 2,
        "tangent_out_bytes": 2,
        "total_bytes": 6,
        "description": "All components 16-bit"
    },
    0x60: {
        "format": "2:1:1",
        "value_bytes": 2,
        "tangent_in_bytes": 1,
        "tangent_out_bytes": 1,
        "total_bytes": 4,
        "description": "16-bit value, 8-bit tangents"
    },
    0x80: {
        "format": "1:4:4",
        "value_bytes": 1,
        "tangent_in_bytes": 4,
        "tangent_out_bytes": 4,
        "total_bytes": 9,
        "description": "8-bit value, float tangents"
    },
    0x90: {
        "format": "1:2:2",
        "value_bytes": 1,
        "tangent_in_bytes": 2,
        "tangent_out_bytes": 2,
        "total_bytes": 5,
        "description": "8-bit value, 16-bit tangents"
    },
    0xA0: {
        "format": "1:1:1",
        "value_bytes": 1,
        "tangent_in_bytes": 1,
        "tangent_out_bytes": 1,
        "total_bytes": 3,
        "description": "1 byte per component"
    },
    0xF0: {
    "format": "4:4:-",
    "value_bytes": 4,
    "tangent_in_bytes": 4,
    "tangent_out_bytes": 0,
    "total_bytes": 8,
    "description": "Float value with shared float tangent (used as both in and out)"
},
}

def get_encoding_info(encoding_byte):
    upper_nibble = encoding_byte & 0xF0
    return FCV_ENCODING_TYPES.get(upper_nibble, None)

def decode_axis_keyframes(data: bytes, encoding_byte: int, frame_ids: list, endianness: str = "<") -> list:
    enc = get_encoding_info(encoding_byte)
    if not enc:
        raise ValueError(f"Invalid encoding byte: 0x{encoding_byte:02X}")

    def unpack_val(fmt, size, off):
        val = struct.unpack_from(fmt, data, off)
        return val[0], off + size

    def _fmt(size, endianness, signed=False):
        if size == 4:
            return endianness + "f"
        elif size == 2:
            return endianness + ("H" if not signed else "h")
        elif size == 1:
            return endianness + ("B" if not signed else "b")
        else:
            raise ValueError(f"Unsupported field size: {size}")

    offset = 0
    per_kf_bytes = enc["value_bytes"] + enc["tangent_in_bytes"] + enc["tangent_out_bytes"]
    result = []

    for i, fid in enumerate(frame_ids):
        if offset + per_kf_bytes > len(data):
            break

        # Unpack raw values
        raw_val, offset = unpack_val(_fmt(enc['value_bytes'], endianness), enc['value_bytes'], offset)
        raw_in, offset = unpack_val(_fmt(enc['tangent_in_bytes'], endianness), enc['tangent_in_bytes'], offset)
        raw_out, offset = unpack_val(_fmt(enc['tangent_out_bytes'], endianness), enc['tangent_out_bytes'], offset)

        # Decode rotation (only if value_bytes == 2)
        if enc['value_bytes'] == 2:
            decoded_val = decode_rotation_uint16(raw_val, signed=True)
        else:
            decoded_val = raw_val

        # Decode Hermite tangents
        decoded_in = decode_hermite_tangent(raw_in, enc['tangent_in_bytes'])
        decoded_out = decode_hermite_tangent(raw_out, enc['tangent_out_bytes'])

        result.append({
            "frame": fid,
            "value": round(decoded_val, 4),
            "in": round(decoded_in, 4),
            "out": round(decoded_out, 4)
        })

    return result

def decode_rotation_uint16(val, signed=False):
    """Convert uint16-encoded rotation value to degrees.

    If signed=False: assumes 0–65535 maps to 0°–360°
    If signed=True: assumes 0–65535 maps to -180° to +180°
    """
    if signed:
        return ((val / 65535.0) * 360.0) - 180.0
    else:
        return (val / 65535.0) * 360.0
        
def convert_degrees_to_radians(keyframe_block):
    """Converts 'value' fields from degrees to radians for all axes in a keyframe block."""
    for axis in ['X', 'Y', 'Z']:
        for kf in keyframe_block["axis_data"][axis]["values"]:
            kf["value"] = round(math.radians(kf["value"]), 6)

def decode_hermite_tangent(raw_val, byte_size, slope_range=10.0, p0=None, p1=None, steps=10):
    """
    Decode Hermite tangent byte(s) into float slope.
    - 4 bytes: treated as float
    - 2/1 bytes: scaled from [-slope_range, +slope_range]
    
    Optionally computes Hermite spline points if p0 and p1 provided.
    """
    # Decode the tangent
    if byte_size == 4:
        slope = raw_val if isinstance(raw_val, float) else unpack("f", pack("I", raw_val))[0]
    elif byte_size == 2:
        slope = ((raw_val / 65535.0) * 2.0 * slope_range) - slope_range
    elif byte_size == 1:
        slope = ((raw_val / 255.0) * 2.0 * slope_range) - slope_range
    else:
        slope = 0.0

    # compute Hermite points for debugging/graphing
    if p0 is not None and p1 is not None:
        hpoints = hermite_spline_points(p0, p1, slope, slope, steps)
        _last_hermite_debug["last_points"] = hpoints
        _last_hermite_debug["clamped"] = is_clamped_slope(slope, slope_range)

    return slope
    
def hermite_spline_points(p0, p1, t0, t1, steps=10):
    result = []
    for i in range(steps + 1):
        t = i / steps
        h00 = 2*t**3 - 3*t**2 + 1
        h10 = t**3 - 2*t**2 + t
        h01 = -2*t**3 + 3*t**2
        h11 = t**3 - t**2
        value = h00 * p0 + h10 * t0 + h01 * p1 + h11 * t1
        result.append(value)
    return result

def is_clamped_slope(val, slope_range=10.0, epsilon=1e-3):
    return abs(abs(val) - slope_range) < epsilon  
