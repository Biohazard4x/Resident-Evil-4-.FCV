
# fcv_data_roles.py
# These Tested on Human IKs
'''
This was made for an older version of the run_fcv script but was revised to be more mimimum.
Im leaving this for future defintions and ussage. 
'''

FCV_DATA_ROLES = {
    0x00: "PULL_LEFT",      # Pulls Local Left
    0x01: "PULL_RIGHT_1",   # Reserved? 
    0x02: "PULL_RIGHT_2",   # Reserved? 
    0x03: "PULL_RIGHT_3",   # Pulls Local Right
    0x04: "PULL_FRONT",     # Pulls Local Front
    0x05: "PULL_BACK",      # Pulls Local Backwards
    0x06: "CAMERA",         # Joint becomes a camera-related node
    0x07: "UNKNOWN",        # Camera oriented Joint specifed in PS2 STABs
    0x08: "UNKNOWN",        # Reserved? 
    0x09: "UNKNOWN",        # Reserved? 
    0x0A: "UNKNOWN",        # Reserved? 
    0x0B: "UNKNOWN",        # Reserved? 
    0x0C: "UNKNOWN",        # Reserved? 
    0x0D: "UNKNOWN",        # Reserved? 
    0x0E: "UNKNOWN",        # Reserved? 
    0x0F: "CAMERA?"         # ? ? ? 
}

def get_data_role(byte):
# Given a full FCV data type byte, extract the lower bit and return the role.
    lower_nibble = byte & 0x0F
    return FCV_DATA_ROLES.get(lower_nibble, "UNKNOWN")
    