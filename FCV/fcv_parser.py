import os
import struct
from .fcv_encoding_types import get_encoding_info, decode_axis_keyframes
from .fcv_camera_roles import is_camera_node, get_camera_role
from .fcv_node_types import get_node_type_flags
from .fcv_data_roles import get_data_role

class FCVParser:
    # Initializes the parser with file path, logging, and data structures.
    def __init__(self, filepath, log_path="fcv_debug.log", verbose=False, endianness="<"):
        self.filepath = filepath
        base_name = os.path.basename(filepath)
        self.log_path = f"{base_name}.log"  
        self.verbose = verbose
        self.endianness = endianness
        self.log = open(self.log_path, "w", encoding="utf-8")
        self.max_time = None
        self.node_count = None
        self.node_types = []
        self.data_types = []
        self.node_ids = []
        self.file_size = None
        self.pointer_table = []
        self.keyframe_blocks = []
        self.camera_roles = {}
        self.node_type_flags = []
        self.data_type_roles = []

    # Writes a message to the log file (and console if verbose).
    def log_print(self, msg):
        self.log.write(msg + "\n")  
        if self.verbose:
            print(msg)
        self.log.flush()


    # Main parsing routine: reads header, node data, pointer table, keyframes.
    def parse(self):
        f = open(self.filepath, "rb")  # Open the binary FCV file for reading.
        try:
            # Read the maximum time value in the animation (16-bit unsigned).
            self.max_time = self.read_u16(f)

            # Read the number of nodes/joints in this file (8-bit unsigned).
            self.node_count = self.read_u8(f)

            self.node_types = []
            self.data_types = []

            # Read node type and data type for each joint/node.
            for _ in range(self.node_count):
                b1 = self.read_u8(f)
                b2 = self.read_u8(f)

                # Handle endianness for node_type and data_type ordering.
                if self.endianness == "<":
                    node_type, data_type = b1, b2
                else:
                    data_type, node_type = b1, b2

                # Store node type and data type for each node.
                self.node_types.append(node_type)
                self.data_types.append(data_type)

                # Determine the node type flags and data type roles (e.g. position, rotation).
                self.node_type_flags.append(get_node_type_flags(node_type))
                self.data_type_roles.append(get_data_role(data_type))

            # Read all node IDs for each joint.
            self.node_ids = [self.read_u8(f) for _ in range(self.node_count)]

            # Align the file position to 4 bytes (skip padding bytes if needed).
            current_offset = f.tell()
            aligned_offset = self.align4(current_offset)
            padding = aligned_offset - current_offset
            if padding > 0:
                f.read(padding)  # Skip any padding bytes.
            self.padding = padding  # Save padding info for summary.

            # Read the total file size. While the game doesn't validate this, I included it just for consistency.
            self.file_size = self.read_u32(f)

            # Read the pointer table
            self.pointer_table = [self.read_u32(f) for _ in range(self.node_count)]

            # Parse each keyframe block by seeking to the pointer and decoding the data.
            for i, ptr in enumerate(self.pointer_table):
                f.seek(ptr)  # Seek to the keyframe block position.
                axis_data = {}
                encoding_info = get_encoding_info(self.data_types[i])  # Get encoding details.

                for axis in ['X', 'Y', 'Z']:
                    # Read the number of frames for this axis.
                    frame_count = self.read_u16(f)

                    # Read each frame ID (time steps).
                    frame_ids = [self.read_u16(f) for _ in range(frame_count)]

                    if encoding_info:
                        # Calculate how many bytes to read per keyframe (value + tangents).
                        per_kf_bytes = (
                            encoding_info["value_bytes"] +
                            encoding_info["tangent_in_bytes"] +
                            encoding_info["tangent_out_bytes"]
                        )
                        # Read all keyframe data for this axis at once.
                        data = f.read(per_kf_bytes * frame_count)
                    else:
                        data = b""  # If no encoding info, no data to read.

                    # Decode the raw data into keyframe values and tangents.
                    decoded = decode_axis_keyframes(
                        data,
                        self.data_types[i],
                        frame_ids,
                        endianness=self.endianness
                    )

                    # Store frames and decoded values for this axis.
                    axis_data[axis] = {
                        "frames": frame_ids,
                        "values": decoded
                    }

                # Save the keyframe block for this joint.
                self.keyframe_blocks.append({
                    "count": max(len(axis_data[a]["frames"]) for a in axis_data),
                    "encoding": encoding_info,
                    "axis_data": axis_data
                })

            # Determine camera roles based on data types and node IDs.
            for i in range(self.node_count):
                if is_camera_node(self.data_types[i]):
                    # Check if node ID is within valid camera roles.
                    if self.node_ids[i] in [0x00, 0x01, 0x02, 0x03, 0x04, 0x05]:
                        self.camera_roles[i] = get_camera_role(self.node_ids[i])
                    else:
                        # Log an error if the camera role is invalid.
                        error_msg = (
                            f"[ERROR] Invalid camera joint: "
                            f"Node ID {self.node_ids[i]} with Data Type 0x{self.data_types[i]:02X}"
                        )
                        self.log_print(error_msg)
                        raise ValueError(error_msg)

            # Print a summary of the parsed data to the log.
            self.dump_summary()

        except Exception as e:
            # If an error occurs during parsing, log the offset and dump the summary.
            current_offset = f.tell()
            hex_offset = f"0x{current_offset:04X}"
            self.dump_summary()
            self.log_print(f"[PARSER ERROR] {str(e)} ({hex_offset})")
            raise
        finally:
            # Always close the file and log, even if an exception is raised.
            f.close()
            self.log.close()

    # Reads 1 byte from the file and unpacks as unsigned 8-bit integer.
    def read_u8(self, f):
        return struct.unpack(self.endianness + "B", f.read(1))[0]

    # Reads 2 bytes from the file and unpacks as unsigned 16-bit integer.
    def read_u16(self, f):
        self._file_offset = f.tell()
        return struct.unpack(self.endianness + "H", f.read(2))[0]

    # Reads 4 bytes from the file and unpacks as unsigned 32-bit integer.
    def read_u32(self, f):
        return struct.unpack(self.endianness + "I", f.read(4))[0]

    # Aligns a given offset to the next multiple of 4 bytes.
    def align4(self, offset):
        return (offset + 3) & ~0x03

    # Calculates the total size of each joint's keyframe data.
    def get_joint_data_sizes(self):
        joint_sizes = []
        for i, block in enumerate(self.keyframe_blocks):
            total_bytes = 0
            encoding_info = block["encoding"]
            for axis in ['X', 'Y', 'Z']:
                axis_data = block["axis_data"][axis]
                frame_count = len(axis_data["frames"])
                count_bytes = 2
                id_bytes = frame_count * 2
                if encoding_info:
                    per_kf_bytes = (
                        encoding_info["value_bytes"] +
                        encoding_info["tangent_in_bytes"] +
                        encoding_info["tangent_out_bytes"]
                    )
                    kf_bytes = per_kf_bytes * frame_count
                else:
                    kf_bytes = 0
                total_bytes += count_bytes + id_bytes + kf_bytes
            joint_sizes.append({
                "joint_index": i,
                "node_id": self.node_ids[i],
                "total_bytes": total_bytes
            })
        return joint_sizes

    # Returns the actual size of the file on disk.
    def get_real_file_size(self):
        with open(self.filepath, "rb") as f:
            f.seek(0, 2)
            return f.tell()

    # Returns a summary dictionary of the parsed file data.
    def get_summary(self):
        return {
            "max_time": self.max_time,
            "node_count": self.node_count,
            "file_size": self.file_size,
            "real_file_size": self.get_real_file_size(),
            "padding": self.padding if hasattr(self, 'padding') else 0
        }

    # Logs a human-readable summary of the parsed data.
    def dump_summary(self):
        self.log_print(f"\n=== FCV HEADER ===")
        self.log_print(f"Max Time      : {self.max_time}")
        self.log_print(f"Node Count    : {self.node_count}")
        self.log_print(f"File Size     : {self.file_size} bytes")
        if hasattr(self, "padding") and self.padding > 0:
            self.log_print(f"Padding       : {self.padding} byte(s)")

        self.log_print(f"\n--- Joint Table ---")
        for i in range(len(self.node_types)):
            line = f"  [{i:02}] Type: 0x{self.node_types[i]:02X} | Data: 0x{self.data_types[i]:02X} | ID: {self.node_ids[i]}"
            if i in self.camera_roles:
                line += f" | Camera Role: {self.camera_roles[i]}"
            self.log_print(line)

        self.log_print(f"\n--- Pointer Table ---")
        for i, ptr in enumerate(self.pointer_table):
            self.log_print(f"  Joint {i:02} -> 0x{ptr:08X}")

        self.log_print(f"\n--- Keyframe Blocks ---")
        for i, block in enumerate(self.keyframe_blocks):
            enc = block['encoding']['format'] if block['encoding'] else "UNKNOWN"
            self.log_print(f"  Joint {i:02} | Encoding: {enc}")
            for axis in ['X', 'Y', 'Z']:
                frames = block["axis_data"].get(axis, {}).get("frames", [])
                self.log_print(f"    {axis} Frames: {frames}")

        self.log_print(f"\n--- Keyframe/Tangent Values ---")
        for i, block in enumerate(self.keyframe_blocks):
            self.log_print(f"Joint: {i:02} | ID: {self.node_ids[i]} | Encoding: {enc}")
            for axis in ['X', 'Y', 'Z']:
                values = block["axis_data"].get(axis, {}).get("values", [])
                self.log_print(f"  {axis} Axis:")
                for v in values:
                    self.log_print(f"    Frame {v['frame']:>3}: Value={v['value']}, In={v['in']}, Out={v['out']}")
                    
    # Serializes the parsed data to a dictionary for external use.
    def to_dict(self):
        return {
            "max_time": self.max_time,
            "node_count": self.node_count,
            "file_size": self.file_size,
            "padding": getattr(self, "padding", None),
            "nodes": [
                {
                    "node_type": nt,
                    "data_type": dt,
                    "id": nid,
                    "camera_role": self.camera_roles.get(i),
                    "data_role": self.data_type_roles[i],
                    "keyframes": self.keyframe_blocks[i] if i < len(self.keyframe_blocks) else {}
                }
                for i, (nt, dt, nid) in enumerate(zip(self.node_types, self.data_types, self.node_ids))
            ]
        }
