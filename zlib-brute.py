import zlib


# open file
path = "Z:\\Docs\\Satisfactory\\Blueprint Analysis\\foundation_raw.sbp"

content_bytes = None

# open file
with open(path, "rb") as f:
    content_bytes = f.read()

i = 0

# try to decompress with different byte offsets
# write into folder
while i < len(content_bytes):
    try:
        decompressed = zlib.decompress(content_bytes[i:])
        with open(f"output_{i}.txt", "w") as f:
            f.write(decompressed)
        break
    except:
        print(f"Failed with offset {i}")
        i += 1
        continue