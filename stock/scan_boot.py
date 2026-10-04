import struct
p = r"E:\k70\stock\vermeer_images_OS3.0.307.0.WNKCNXM_16.0\images\boot.img"
data = open(p, "rb").read()
magic = data[0:8]
print("boot magic:", magic)
ver = struct.unpack_from("<I", data, 8)[0]
ksize = struct.unpack_from("<I", data, 12)[0]
page = struct.unpack_from("<I", data, 36)[0]
hdr_ver = ver
print(f"boot header ver={ver} kernel_size={ksize} page={page}")
# scan whole image for FDT magics
starts = []
i = 0
while len(starts) < 30:
    i = data.find(bytes.fromhex("d00dfeed"), i)
    if i < 0: break
    starts.append(i); i += 4
print("FDT magics in boot.img:", starts[:20])
for s in starts[:6]:
    try:
        ts = struct.unpack_from(">I", data, s+4)[0]
        print(f"  at {s}: totalsize={ts}")
    except Exception: pass
