
# fcv_node_types.py
# Node Type bitflag Interp



FCV_NODE_TYPES = {
    0x01: "Root Position",   # Root Handler for position
    0x02: "FK Rotation ",    # Rotation (Relative)
    0x04: "IK Handle",       # Translation (Relative)
    0x08: "Scale",           # Scale (Relative)
    0x10: "IK Parent(?)",          # IK Parent; Need to check when and how the game uses this
    0x20: "IK Toe Parent",          # IK Parent specifically for feet 
    0x40: "Root Rotation",   # Root Handler but for rotation
    0x80: "Bone Flip",        # Flip Bone (mirroring)
    0xA0: "IK Arm Parent",           # IK Parent for Arms 
}

def get_node_type_flags(byte):
   
   #   Returns a list of short flag labels for a node type byte.
    return [label for bit, label in FCV_NODE_TYPES.items() if byte & bit]
