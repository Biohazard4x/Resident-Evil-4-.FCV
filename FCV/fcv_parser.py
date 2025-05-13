
# fcv_parser.py
# This is the main parser for the FCV technical stuff involving the keyframes is done in fcv_encoding_types.py
# the other py modules are left over and not used here. 

import struct
from .fcv_encoding_types import get_encoding_info, decode_axis_keyframes
from .fcv_camera_roles import is_camera_node, get_camera_role

class FCVParser:
    def __init__(self, filepath, log_path="fcv_debug.log", verbose=False):
        self.filepath = filepath
        self.log_path = log_path
        self.verbose = verbose
        self.log = open(log_path, "w", encoding="utf-8")
        self.max_time = None
        self.node_count = None
        self.node_types = []
        self.data_types = []
        self.node_ids = []
        self.file_size = None
        self.pointer_table = []
        self.keyframe_blocks = []
        self.camera_roles = {}

    def log_print(self, msg):
        if self.verbose:
            print(msg)
        self.log.write(msg + "\n")

    def read_u8(self, f):
        return struct.unpack("<B", f.read(1))[0]

    def read_u16(self, f):
        return struct.unpack("<H", f.read(2))[0]

    def read_u32(self, f):
        return struct.unpack("<I", f.read(4))[0]

    def align4(self, offset):       # Aligns the padding bytes of header to a 32Bit boundary
        return (offset + 3) & ~0x03

    def parse(self):
        with open(self.filepath, "rb") as f:
            self.max_time = self.read_u16(f)
            self.node_count = self.read_u8(f)
            self.node_types = []
            self.data_types = []
            for _ in range(self.node_count):
                self.node_types.append(self.read_u8(f))
                self.data_types.append(self.read_u8(f))
            self.node_ids = [self.read_u8(f) for _ in range(self.node_count)]

            current_offset = f.tell()
            aligned_offset = self.align4(current_offset)
            padding = aligned_offset - current_offset
            if padding > 0:
                f.read(padding)
                
            self.padding = padding
                
            self.file_size = self.read_u32(f)   # I dont think the game uses this, but it must be present even if nulled   
            self.pointer_table = [self.read_u32(f) for _ in range(self.node_count)]

            for i, ptr in enumerate(self.pointer_table):
                f.seek(ptr)
                axis_data = {}
                encoding_info = get_encoding_info(self.data_types[i])

                for axis in ['X', 'Y', 'Z']:
                    frame_count = self.read_u16(f)
                    frame_ids = [self.read_u16(f) for _ in range(frame_count)]

                    if encoding_info:
                        per_kf_bytes = (
                            encoding_info["value_bytes"] +
                            encoding_info["tangent_in_bytes"] +
                            encoding_info["tangent_out_bytes"]
                        )
                        data = f.read(per_kf_bytes * frame_count)
                    else:
                        data = b""


                    decoded = decode_axis_keyframes(data, self.data_types[i], frame_ids)
                    axis_data[axis] = {
                        "frames": frame_ids,
                        "values": decoded
                    }


                self.keyframe_blocks.append({
                    "count": max(len(axis_data[a]["frames"]) for a in axis_data),
                    "encoding": encoding_info,
                    "axis_data": axis_data
                })

            for i in range(self.node_count):
                if is_camera_node(self.data_types[i]):
                    if self.node_ids[i] in [0x00, 0x01, 0x02, 0x03, 0x04, 0x05]:
                        self.camera_roles[i] = get_camera_role(self.node_ids[i])
                    else:
                        error_msg = f"[ERROR] Invalid camera joint: Node ID {self.node_ids[i]} with Data Type 0x{self.data_types[i]:02X}"
                        self.log_print(error_msg)
                        self.log.close()
                        raise ValueError(error_msg)
            self.log_print(f"\n=== FCV HEADER ===")
            self.log_print(f"Max Time      : {self.max_time}")
            self.log_print(f"Node Count    : {self.node_count}")
            self.log_print(f"File Size     : {self.file_size} bytes")
            if padding > 0:
                self.log_print(f"Padding       : {padding} byte(s) (to align to 4-byte boundary)")

            self.log_print(f"\n--- Joint Table ---")
            for i in range(self.node_count):
                line = f"  [{i:02}] Type: 0x{self.node_types[i]:02X} | Data: 0x{self.data_types[i]:02X} | ID: {self.node_ids[i]}"
                if i in self.camera_roles:
                    line += f" ↳ Camera Role: {self.camera_roles[i]}"
                self.log_print(line)

            self.log_print(f"\n--- Pointer Table ---")
            for i, ptr in enumerate(self.pointer_table):
                self.log_print(f"  Joint {i:02} -> 0x{ptr:08X}")

            self.log_print(f"\n--- Keyframe Blocks ---")
            for i, block in enumerate(self.keyframe_blocks):
                enc = block['encoding']['format'] if block['encoding'] else "UNKNOWN"
                self.log_print(f"  Joint {i:02} | Keys: {block['count']} | Encoding: {enc}")
                for axis in ['X', 'Y', 'Z']:
                    frames = block["axis_data"].get(axis, {}).get("frames", [])
                    self.log_print(f"    {axis} Frames: {frames}")


        self.log_print(f"\n--- Keyframe/Tangent Values ---")
        for i, block in enumerate(self.keyframe_blocks):
            self.log_print(f"Joint: {i:02} | ID: {self.node_ids[i]} | Keys: {block['count']}")
            for axis in ['X', 'Y', 'Z']:
                values = block["axis_data"].get(axis, {}).get("values", [])
                self.log_print(f"  {axis} Axis:")
                for v in values:
                    self.log_print(f"    Frame {v['frame']:>3}: Value={v['value']}, In={v['in']}, Out={v['out']}")

        self.log.close()
        
        #Displays in the run_fcv.py 
    def get_summary(self): 
        return {
            "max_time": self.max_time,
            "node_count": self.node_count,
            "file_size": self.file_size,
            "padding": self.padding if hasattr(self, 'padding') else 0
        }