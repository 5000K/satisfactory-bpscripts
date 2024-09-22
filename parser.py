import json
import zlib

from BufferReader import BufferReader
from reader import BpBodyReader

# open file
path = r"Z:\Docs\Satisfactory\Blueprint Analysis\foundation_concrete+normal.sbp"

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

# read objects
objects = BpBodyReader().read(body_reader)

print("\nBody Data ============================================================================")

# dump to json
for obj in objects:
    print(obj.dump_to_json())
