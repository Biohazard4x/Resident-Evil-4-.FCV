
# fcv_camera_roles.py
# Defines Camera Roles in the debug log and does some logic to determine camera role between joints

def is_camera_node(data_type_byte):
    return (data_type_byte & 0x0F) == 0x06

def get_camera_role(node_id):
    roles = {
        0x00: "Camera Position",
        0x01: "Camera Target",
        0x02: "Camera Roll",
        0x03: "Camera Field of View",
        0x04: "Camera Speed (?)",
        0x05: "Unknown Camera"
    }
    return roles.get(node_id, None)

def detect_camera_roles(node_ids, data_types):
    camera_roles = {}
    for i, (nid, dtype) in enumerate(zip(node_ids, data_types)):
        if is_camera_node(dtype):
            role = get_camera_role(nid)
            if role is not None:
                camera_roles[i] = role
            else:
                raise ValueError(f"[ERROR] Invalid camera joint: Node ID {nid} with Data Type 0x{dtype:02X}")
    return camera_roles