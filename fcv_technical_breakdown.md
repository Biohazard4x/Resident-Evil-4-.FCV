
# FCV (Frames, Curves, Values) Technical Format Breakdown  
**Game**: Resident Evil 4 (2005)  
**File Type**: Binary  
**Purpose**: Encodes animation data for bones, joints, and camera systems using Hermite spline keyframes.  
**Design**: Structurally optimized for runtime interpolation with predictable, pointer-based parsing.

---

## 1. Structural Overview

The FCV file is divided into four main components:

1. **Header**
2. **Node Metadata (packed entries)**
3. **Joint ID List**
4. **Pointer Table and Keyframe Data Blocks**

All data is aligned to a 16-byte boundary after the header. The FCV file is parsed strictly in memory based on this fixed layout.

---

## 2. FCV Header (Offset 0x00–0x0F)

| Offset | Size | Type     | Description |
|--------|------|----------|-------------|
| 0x00   | 2    | `uint16` | Max Time (in frames) — defines FCV animation length |
| 0x02   | 1    | `uint8`  | Node Count — number of joint entries to process |
| 0x03   | N    | `uint8[]`| Node Types — one per joint (transformation behavior) |
| 0x03+N | N    | `uint8[]`| Data Types — one per joint (encoding + special flags) |
| 0x03+2N| N    | `uint8[]`| Node IDs — bone/joint identifiers used by engine |
| 0x03+3N| 4    | `uint32` | File Size — always read, can be zero |
| 0x03+3N+4| 0–15 | padding | Zeroes added to align to 16-byte boundary |
| ALIGN  | 4×N  | `uint32[]`| Pointers to keyframe blocks for each joint |

---

## 3. Packed Node Entries

Each joint is defined by a **packed pair** of:
- **Node Type**: Describes transformation behavior (e.g., translation, rotation, scale)
- **Data Type**: Encodes both curve compression type and interpretation flags

### Node Type Flags (bitmask):

| Value | Name               | Description |
|-------|--------------------|-------------|
| 0x01  | Player Controller  | Used in gameplay; moves PC/NPC across world space |
| 0x02  | Rotation (Relative)| FK-style animation |
| 0x04  | Translation (Relative)| IK-style motion |
| 0x08  | Scale (Relative)   | Uniform/local scale changes |
| 0x10  | Rotation (Absolute)| World rotation |
| 0x20  | Translation (Absolute)| World translation |
| 0x40  | Scale (Absolute)   | World scale |
| 0x80  | Flip Bone          | Used for mirror transformations |

---

## 4. Data Type Byte

Split into:
- **Upper Nibble** = Curve Encoding Type
- **Lower Nibble** = IK Pull Direction or Camera Role

### Upper Nibble — Encoding Types

| Value | Axis Format | Description           | Total Size |
|--------|-------------|------------------------|-------------|
| 0x00   | 4:4:4       | Float X, Y, Z          | 12 bytes |
| 0x10   | 4:2:2       | Mixed float/int16      | 8 bytes |
| 0x20   | 4:1:1       | Mixed float/int8       | 6 bytes |
| 0x40   | 2:4:4       | Mixed int16/float      | 10 bytes |
| 0x50   | 2:2:2       | All int16              | 6 bytes |
| 0x60   | 2:1:1       | Mixed int16/int8       | 4 bytes |
| 0x90   | 1:2:2       | Mixed int8/int16       | 5 bytes |
| 0xA0   | 1:1:1       | All int8               | 3 bytes |

### Lower Nibble — IK Pull or Camera Mode

| Value | Meaning |
|-------|---------|
| 0x00–0x05 | IK Pull direction (Left, Right, Front, Back) |
| 0x06  | **Camera Node** — Joint becomes camera-affiliated |
| 0x07+ | Reserved |

---

## 5. Camera Node Behavior

If a joint’s **Data Type** has lower nibble = 0x06, it’s a **camera node**. Valid Node IDs: 0x00–0x05

| ID | Role            | Notes |
|----|------------------|-------|
| 00 | Camera Position  | XYZ controls camera position |
| 01 | Camera Target    | XYZ controls look-at |
| 02 | Camera Roll      | Y-axis drives roll |
| 03 | Camera FOV       | Y-axis controls FOV |
| 04 | Camera Speed     | Controls blend/speed (Y-axis) |
| 05 | Unknown          | Behavior unclear |

Even single-value channels require full XYZ bind poses.

---

## 6. Pointer Table

- After the header is aligned to 16 bytes, each joint has a 4-byte pointer.
- These offsets point to the **start of the keyframe block** for each joint.
- Pointer count must match the number of joints.

---

## 7. Keyframe Data Blocks (Per Axis)

Each joint has 3 axis tracks (X, Y, Z). Each track is structured:

| Offset | Type     | Description |
|--------|----------|-------------|
| 0x00   | `uint16` | Keyframe Count |
| 0x02   | `uint16` | Start Frame Index |
| 0x04   | `byte[]` | Encoded keyframe values and tangents (Hermite or baked) |

- Encoding format is dictated by Data Type byte.
- If values are baked, they are stored per frame with no curve.
- If Hermite, values and tangents are stored per keyframe.

---

## 8. Engine Behavior

- FCV files are parsed strictly in memory: no dynamic structure or tags.
- The engine expects the following:
  - `File Size` is read (even if unused)
  - `Padding` is calculated after reading the header to ensure alignment
  - Keyframe data must match joint count × 3 axes
- Camera motion only activates if `DataType & 0x0F == 0x06`
- Each joint must supply full XYZ data—even if only one axis is animated.

---

## 9. Cutscene vs Gameplay

| Mode     | Behavior |
|----------|----------|
| Gameplay | Uses SEQ + FCV. SEQ sets timeline duration and event triggers |
| Cutscene| FCV only. Speed baked in, sound controlled via SFX |

---

## Summary

The FCV format in RE4 is a highly optimized, low-level animation system using Hermite spline interpolation and memory-aligned pointer tables. It supports dynamic motion for gameplay, camera systems, and cutscenes while enforcing strict runtime parsing logic.

