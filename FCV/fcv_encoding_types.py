# fcv_encoding_types.py (Cleaned)
# Provides encoding metadata and decodes keyframe triplets per axis

import struct

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
}
# Grabs the Lower Bit of the Encoding byte and stores it. 
def get_encoding_info(encoding_byte):
    upper_nibble = encoding_byte & 0xF0
    return FCV_ENCODING_TYPES.get(upper_nibble, None)

def decode_axis_keyframes(data: bytes, encoding_byte: int, frame_ids: list) -> list:
    enc = get_encoding_info(encoding_byte)
    if not enc:
        raise ValueError(f"Invalid encoding byte: 0x{encoding_byte:02X}")

    def unpack_val(fmt, size, off):
        val = struct.unpack_from(fmt, data, off)
        return val[0], off + size

    def _fmt(size):
        if size == 4:
            return "<f"
        elif size == 2:
            return "<h"
        elif size == 1:
            return "<b"
        else:
            raise ValueError(f"Unsupported field size: {size}")

    #This is taking the keyframe values and assocating them to their proper ussage names
    offset = 0
    per_kf_bytes = enc["value_bytes"] + enc["tangent_in_bytes"] + enc["tangent_out_bytes"]
    result = []
    for i, fid in enumerate(frame_ids):
        if offset + per_kf_bytes > len(data):
            break
        value, offset = unpack_val(_fmt(enc['value_bytes']), enc['value_bytes'], offset)
        tan_in, offset = unpack_val(_fmt(enc['tangent_in_bytes']), enc['tangent_in_bytes'], offset)
        tan_out, offset = unpack_val(_fmt(enc['tangent_out_bytes']), enc['tangent_out_bytes'], offset)
        result.append({
            "frame": fid,
            "value": round(value, 4),
            "in": round(tan_in, 4),
            "out": round(tan_out, 4)
        })
    return result
