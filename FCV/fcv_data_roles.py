
# fcv_data_roles.py
# These Tested on Human IKs

FCV_DATA_ROLES = {
    0x00: "UP",             # y = 1.0
    0x01: "DOWN",           # y = -1.0
    0x02: "FORWARD",        # x = 1.0
    0x03: "BACKWARD",       # x = -1.0
    0x04: "LEFT",           # z = 1.0
    0x05: "RIGHT",          # z = -1.0
    0x06: "CAMERA",         # Joint becomes a camera-related node
    0x07: "CAMERA v2",      # Camera oriented Joint specifed in PS2 STABs
    0x08: "INVALID",        # Reserved? 
    0x09: "INVALID",        # Reserved? 
    0x0A: "INVALID",        # Reserved? 
    0x0B: "INVALID",        # Reserved? 
    0x0C: "INVALID",        # Reserved? 
    0x0D: "INVALID",        # Reserved? 
    0x0E: "INVALID",        # Reserved? 
    0x0F: "INVALID"         # Reserved? 
}

def get_data_role(byte):
# Given a full FCV data type byte, extract the lower bit and return the role.
    lower_nibble = byte & 0x0F
    return FCV_DATA_ROLES.get(lower_nibble, "INVALID")
    