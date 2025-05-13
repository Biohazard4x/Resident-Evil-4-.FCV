
# fcv_node_types.py
#Use this for efficient flag interpretation.
'''
This was made for an older version of the run_fcv script but was revised to be more mimimum.
Im leaving this for future defintions and ussage. 
'''

FCV_NODE_TYPES = {
    0x01: "PC_CTRL",    # Player Controller
    0x02: "ROT_REL",    # Rotation (Relative)
    0x04: "TRANS_REL",  # Translation (Relative)
    0x08: "SCALE_REL",  # Scale (Relative)
    0x10: "ROT_ABS",    # Rotation (Absolute)
    0x20: "TRANS_ABS",  # Translation (Absolute)
    0x40: "SCALE_ABS",  # Scale (Absolute)
    0x80: "FLIP_BONE"   # Flip Bone (mirroring)
}

def get_node_type_flags(byte):
   
   #   Returns a list of short flag labels for a node type byte.
    return [label for bit, label in FCV_NODE_TYPES.items() if byte & bit]
