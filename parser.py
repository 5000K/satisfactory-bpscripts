import json
import zlib

from BufferReader import BufferReader

# open file
path = r"Z:\Docs\Satisfactory\Blueprint Analysis\foundation_raw_offset1.sbp"

# open file
with open(path, "rb") as f:
    content_bytes = f.read()

outputfile = open("output.bin", "wb")


content_reader = BufferReader(content_bytes)

# Header
metadata = (content_reader.next_int32(), content_reader.next_int32(), content_reader.next_int32())
print(f"Metadata: {metadata}")

dimensions = (content_reader.next_int32() * 8, content_reader.next_int32() * 8, content_reader.next_int32() * 8)
print(f"Size: {dimensions[0]}m x {dimensions[1]}m x {dimensions[2]}m")


# 1. materials
amount = content_reader.next_int32()
content_reader.skip_forward(4)  # skip 4 null bytes

print("Materials ============================================================================")

for i in range(amount):
    mat_id = content_reader.next_string()

    # read amount: 4 bytes
    amount = content_reader.next_int32()

    print(f"\t{amount} x {mat_id}")

    # skip 4 null bytes
    content_reader.skip_forward(4)

# revert last offset change
content_reader.skip_backwards(4)

print("\nBuilding Types =======================================================================")

# 2. Buildings
amount = content_reader.next_int32()
content_reader.skip_forward(4)  # skip 4 null bytes

for i in range(amount):
    building_id = content_reader.next_string()

    print(f"\t{building_id}")

    # skip 4 null bytes
    content_reader.skip_forward(4)


# revert last offset change
content_reader.skip_backwards(4)

# 3. Building data (Compressed)
# For now, assuming compression with zlib.

signature = content_reader.next_int32()
assert signature == 2653586369, f"Invalid signature: {signature}"

archive_header = content_reader.next_int32()
assert archive_header == 0x22222222, f"Invalid archive header: {archive_header}"

max_chunk_size = content_reader.next_int64()
assert max_chunk_size == 128 * 1024, f"Invalid max chunk size: {max_chunk_size}"

algorithm = content_reader.next_byte()
assert algorithm == 3, f"Invalid algorithm: {algorithm}"  # assume always zlib

compressed_size = content_reader.next_int64()

decompressed_size = content_reader.next_int64()

assert compressed_size == content_reader.next_int64(), "Compressed size mismatch"
assert decompressed_size == content_reader.next_int64(), "Decompressed size mismatch"


# decompress
compressed_data = content_reader.next_bytes(compressed_size)
decompressed = zlib.decompress(compressed_data)
# output to file
outputfile.write(decompressed)

# someone complained.
outputfile.close()


# let's use the decompressed data
body_reader = BufferReader(decompressed)

actual_body_size = body_reader.next_int32()
# check if no data is out of bounds
assert actual_body_size <= len(decompressed), f"Invalid body size: {actual_body_size} != {len(decompressed)}"

unknown_field = body_reader.next_int32()
object_count = body_reader.next_int32()

print("\nMetadata =============================================================================")


def parse_object_property(reader: BufferReader, prop_name: str):
    size = reader.next_int32()
    reader.skip_forward(5)  # skip 5 null bytes

    return {"name": prop_name, "levelName": reader.next_string(), "pathName": reader.next_string()}


def parse_struct_property(reader: BufferReader, prop_name: str):
    prop = {"name": prop_name}
    size = reader.next_int32()
    reader.skip_forward(4)  # skip 4 null bytes
    prop["structType"] = reader.next_string()
    prop["values"] = {}

    # skip padding
    reader.skip_forward(8 + 8 + 1)  # offset is 2 longs, 1 byte

    if prop["structType"] == "Color":
        prop["values"]["r"] = reader.next_byte()
        prop["values"]["g"] = reader.next_byte()
        prop["values"]["b"] = reader.next_byte()
        prop["values"]["a"] = reader.next_byte()

    elif prop["structType"] == "LinearColor":
        prop["values"]["r"] = reader.next_float()
        prop["values"]["g"] = reader.next_float()
        prop["values"]["b"] = reader.next_float()
        prop["values"]["a"] = reader.next_float()

    elif prop["structType"] == "Vector" or prop["structType"] == "Rotator":
        prop["values"]["x"] = reader.next_float()
        prop["values"]["y"] = reader.next_float()
        prop["values"]["z"] = reader.next_float()

    elif prop["structType"] == "Vector2D":
        prop["values"]["x"] = reader.next_float()
        prop["values"]["y"] = reader.next_float()

    elif prop["structType"] == "Vector4" or prop["structType"] == "Quat":
        prop["values"]["x"] = reader.next_float()
        prop["values"]["y"] = reader.next_float()
        prop["values"]["z"] = reader.next_float()
        prop["values"]["w"] = reader.next_float()

    # parse as generic struct type (=> nested properties)
    prop["values"]["value"] = []

    while True:
        sub_prop = parse_property(reader)

        if sub_prop is None:
            break

        prop["values"]["value"].append(sub_prop)

    return prop


def parse_property(reader: BufferReader) -> dict or None:
    prop_name = reader.next_string()
    if prop_name == "None":
        return None

    prop_type = reader.next_string()

    prop = None

    if prop_type == "ObjectProperty":
        prop = parse_object_property(reader, prop_name)
    elif prop_type == "StructProperty":
        prop = parse_struct_property(reader, prop_name)

    else:
        raise Exception(f"Unknown property type: {prop_type}")

    prop["type"] = prop_type

    return prop


def parse_properties(reader):
    properties = []
    was_none = False

    while not was_none:
        prop = parse_property(reader)
        if prop is None:
            if was_none:
                break
            was_none = True
        else:
            properties.append(prop)
            was_none = False

    return properties


for i in range(object_count):
    obj_type = body_reader.next_int32()
    obj_header = {}

    obj = {"header": obj_header}

    if obj_type == 1:
        obj_header["typePath"] = body_reader.next_string()
        obj_header["root"] = body_reader.next_string()
        obj_header["instanceName"] = body_reader.next_string()
        obj_header["needTransform"] = body_reader.next_int32() == 1
        obj_header["rotX"] = body_reader.next_float()
        obj_header["rotY"] = body_reader.next_float()
        obj_header["rotZ"] = body_reader.next_float()
        obj_header["rotW"] = body_reader.next_float()

        obj_header["posX"] = body_reader.next_float()
        obj_header["posY"] = body_reader.next_float()
        obj_header["posZ"] = body_reader.next_float()

        obj_header["scaleX"] = body_reader.next_float()
        obj_header["scaleY"] = body_reader.next_float()
        obj_header["scaleZ"] = body_reader.next_float()

        obj_header["placedInLevel"] = body_reader.next_string() == 1

        uk1 = body_reader.next_int32()
        uk2 = body_reader.next_int32()
        uk3 = body_reader.next_int32()

        obj["parentRoot"] = body_reader.next_string()
        obj["parentObjectName"] = body_reader.next_string()

        body_reader.skip_forward(4)  # skip 4 null bytes

        props = parse_properties(body_reader)
        obj["properties"] = props

        print(json.dumps(obj, indent=4))

