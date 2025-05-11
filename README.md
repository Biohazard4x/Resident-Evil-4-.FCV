
# FCV (Frames, Curves, Values) Animation File Format Specification  
**Game**: Resident Evil 4 (2005) 
**File Type**: Binary  
**Purpose**: Defines animation for bones, camera, and player movement using keyframes and Hermite curves. No raw 3D data is stored.
**Ports**: PS2/Ubisoft/UHD
**Notes**: This is based for the above ports. UHD file size is big endian. The GameCube port is entirely big endian.

---

## File Structure Overview

1. **FCV Header**
2. **Node Metadata (Packed: Node Type + Data Type)**
3. **Joint IDs**
4. **Pointer Table to Keyframe Blocks**
5. **Keyframe Blocks (per axis, per joint)**

---

## 1. FCV Header

| Offset | Type     | Description |
|--------|----------|-------------|
| 0x00   | uint16   | Max Time (in frames) |
| 0x02   | uint8    | Node Count (number of animated joints) |
| 0x03   | uint8[]  | Node Types (1 byte per node, see Node Type table) |
| 0x04   | uint8[]  | Data Types (1 byte per node, upper and lower nibbles, see below) |
| 0x05   | uint8[]  | Joint IDs (1 byte per node) |
| 0x06   | uint32   | File Size (always read, can be zero) |
| 0x0A   | padding  | Optional padding to 16-byte boundary |
| 0x0B   | uint32[] | Pointers to keyframe data blocks (1 per joint) |

**Note**: Node Types and Data Types form a packed structure and correspond 1:1 with Joint IDs and Pointers.

---

## 2. Node Type Flags

These define the function or transformation type of each node.

| Value   | Name             | Description |
|---------|------------------|-------------|
| 0x01    | Player Controller (PC) | Controls player/enemy in-game movement |
| 0x02    | Rotation (Relative)   | FK rotation |
| 0x04    | Translation (Relative)| IK translation |
| 0x08    | Scale (Relative)      | Local scale |
| 0x10    | Rotation (Absolute)   | Possibly world rotation |
| 0x20    | Translation (Absolute)| Possibly world translation |
| 0x40    | Scale (Absolute)      | Possibly world scale |
| 0x80    | Flip Bone             | For left/right handed bone flipping |

These flags can be combined as bitmasks.

---

## 3. Data Type (Encoding Format + IK Pull/Camera Flags)

Each Data Type byte contains two nibbles:  
- **Upper nibble** = Encoding type (curve data structure)  
- **Lower nibble** = IK Pull direction OR camera usage flag

### **Upper Nibble (Keyframe Encoding Types)**

| Upper | Format                       | Axis Ratio     | Total Size |
|--------|------------------------------|----------------|-------------|
| 0x00   | Float, Float, Float          | 4:4:4          | 12 bytes |
| 0x10   | Float, int16, int16          | 4:2:2          | 8 bytes |
| 0x20   | Float, int8, int8            | 4:1:1          | 6 bytes |
| 0x40   | int16, Float, Float          | 2:4:4          | 10 bytes |
| 0x50   | int16, int16, int16          | 2:2:2          | 6 bytes |
| 0x60   | int16, int8, int8            | 2:1:1          | 4 bytes |
| 0x90   | int8, int16, int16           | 1:2:2          | 5 bytes |
| 0xA0   | int8, int8, int8             | 1:1:1          | 3 bytes |

### **Lower Nibble (IK Pull Direction / Camera Assignment)**

| Value | Meaning |
|-------|---------|
| 0x00  | IK Pull: Player's Left |
| 0x01  | IK Pull: Player's Right |
| 0x02  | IK Pull: Player's Right |
| 0x03  | IK Pull: Player's Right |
| 0x04  | IK Pull: Player's Front |
| 0x05  | IK Pull: Player's Back |
| 0x06  | **Camera Type**: This node is camera-related |
| 0x07+ | Reserved / Unknown |

---

## 4. Camera Node Definitions

If a joint's data type lower nibble is 0x06, it's considered a camera node. Only the following Joint IDs are used:

| Joint ID | Name             | Function |
|----------|------------------|----------|
| 0x00     | Camera Position  | World-space camera position |
| 0x01     | Camera Target    | Look-at point |
| 0x02     | Camera Roll      | Controlled by Y-axis |
| 0x03     | Camera FOV       | Controlled by Y-axis |
| 0x04     | Camera Speed     | Unknown effect |
| 0x05     | Unknown          | Unused or special-case |

---

## 5. Keyframe Data Blocks

Each axis (X, Y, Z) of a joint gets its own keyframe block. The pointer table in the header tells where each block starts.

### **FCV Keyframe Block Format**

| Offset | Type     | Description |
|--------|----------|-------------|
| 0x00   | uint16   | Keyframe Count |
| 0x02   | uint16   | Keyframe Start Frame |
| 0x04   | byte[]   | Keyframe Curve Data (Hermite splines or direct baked data) |

- The encoding format is determined by the jointâs Data Type (see table above).
- Even if an axis is static or unused, it **must** be present with start/end bind pose values.

---

## 6. Padding

To maintain alignment, the header (up to pointer table) must be padded to a **16-byte boundary**.  
If the calculated size isnât aligned, zero bytes are inserted.  
**This padding is always expected and must be respected**âomitting it will break file parsing.

---

## Parsing Notes

- Each Node Type/Data Type pair corresponds to one Joint ID and one Pointer.
- Node Type and Data Type should be treated as packed structures (not interleaved).
- Bind poses must always be defined per axis (X, Y, Z), even if only one is used.
- Any unused nodes should be removed to save space.
- The game will always read the file size field but does not validate its value.

---

## Summary

FCV is a compact and rather rigid animation format but behind this make its a very versatile, optimized format reducing complex animations as small as 5kb if pushed far enough. 