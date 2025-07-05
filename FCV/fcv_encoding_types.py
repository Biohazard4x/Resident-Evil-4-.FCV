import struct
import math


# FCV_ENCODING_TYPES dictionary defines various formats for keyframe encoding.
# Each key is a unique encoding byte, with value specifying how many bytes each component uses.
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
    """
    Looks up the FCV encoding configuration based on the upper nibble of the encoding byte.
    This groups encodings logically if multiple variations share similar upper nibble values.
    """
    upper_nibble = encoding_byte & 0xF0
    return FCV_ENCODING_TYPES.get(upper_nibble, None)

def decode_axis_keyframes(data: bytes, encoding_byte: int, frame_ids: list, endianness: str = "<") -> list:
    """
    Decodes keyframes for a single axis based on the provided encoding byte.
    Extracts value, in-tangent, and out-tangent data, converting them into their proper value formats.
    """
    enc = get_encoding_info(encoding_byte)
    if not enc:
        raise ValueError(f"Invalid encoding byte: 0x{encoding_byte:02X}")

    def unpack_val(fmt, size, off):
        """
        Helper function: unpacks a value from bytes at the given offset and returns updated offset.
        """
        val = struct.unpack_from(fmt, data, off)
        return val[0], off + size

    def _fmt(size, endianness, signed=True):
        """
        Determines struct unpack format string based on size and endianness.
        """
        if size == 4:
            return endianness + "f"
        elif size == 2:
            return endianness + ("H" if not signed else "h")
        elif size == 1:
            return endianness + ("B" if not signed else "b")
        elif size == 0:
            return None  # Indicates no data to unpack    
        else:
            raise ValueError(f"Unsupported field size: {size}")

    offset = 0
    per_kf_bytes = enc["value_bytes"] + enc["tangent_in_bytes"] + enc["tangent_out_bytes"]
    result = []

    for i, fid in enumerate(frame_ids):
        if offset + per_kf_bytes > len(data):
            break  # Prevent reading past end of data

        raw_val, offset = unpack_val(_fmt(enc['value_bytes'], endianness), enc['value_bytes'], offset)
        raw_in, offset = unpack_val(_fmt(enc['tangent_in_bytes'], endianness), enc['tangent_in_bytes'], offset)

        if enc['tangent_out_bytes'] > 0:
            raw_out, offset = unpack_val(_fmt(enc['tangent_out_bytes'], endianness), enc['tangent_out_bytes'], offset)
        else:
            raw_out = raw_in  # Use shared tangent

        # Decode value
        """
        did some wild stuff here and just scrapped ALL OF IT 
        just did this instead becasuse EzPz
        """
        if enc['value_bytes'] == 2:
            decoded_val = raw_val / 10000.0
        else:
            decoded_val = raw_val


        decoded_in = decode_hermite_tangent(raw_in, enc['tangent_in_bytes'])
        decoded_out = decode_hermite_tangent(
            raw_out,
            enc['tangent_in_bytes'] if enc['tangent_out_bytes'] == 0 else enc['tangent_out_bytes']
        )

        result.append({
            "frame": fid,
            "value": round(decoded_val, 4),
            "in": round(decoded_in, 4),
            "out": round(decoded_out, 4)
        })

    return result

        
def convert_degrees_to_radians(keyframe_block):
    """
    Converts 'value' fields in a keyframe block from degrees to radians for each axis.
    """
    for axis in ['X', 'Y', 'Z']:
        for kf in keyframe_block["axis_data"][axis]["values"]:
            kf["value"] = round(math.radians(kf["value"]), 6)
            
def convert_radians_to_degrees(keyframe_block):
    """
    Converts 'value' fields in a keyframe block from radians to degrees for each axis.
    """

    for axis in ['X', 'Y', 'Z']:
        for kf in keyframe_block["axis_data"][axis]["values"]:
            kf["value"] = round(math.degrees(kf["value"]), 6)


def decode_hermite_tangent(raw_val, byte_size, slope_range=0.001):
    """
    Decodes a Hermite tangent value from bytes into a float slope.
    Adjusted for flat-start unsigned 1-byte encoding (0x00 = flat).
    """
    if byte_size == 4:
        slope = raw_val if isinstance(raw_val, float) else unpack("f", pack("I", raw_val))[0]
    elif byte_size == 2:
    # Map uint16 range to slope range
        slope = raw_val / 10000.0
    elif byte_size == 1:
        slope = (raw_val / 255.0) * slope_range
        slope = float(f"{slope:.6f}")
    else:
        slope = 0.0

    return slope
    
def decode_hermite_tangent_with_encoding(raw_val, byte_size, encoding_byte):
    """
    Decodes with auto slope range selection based on encoding byte.
    """
    if encoding_byte == 0x60:
        slope_range = 0.001  # 0x00 = flat
    else:
        slope_range = 100000.0
    return decode_hermite_tangent(raw_val, byte_size, slope_range)

    
def is_clamped_slope(val, slope_range=10.0, epsilon=1e-3):
    """
    Checks if a tangent value is close to the max/min slope range.
    Used to detect 'clamped' tangents for debugging or validation.
    """
    return abs(abs(val) - slope_range) < epsilon  
