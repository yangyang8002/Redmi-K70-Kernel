import struct

p = r"E:\k70\stock\vermeer_images_OS3.0.307.0.WNKCNXM_16.0\images\dtbo.img"
data = open(p, "rb").read()
magic = struct.unpack_from(">I", data, 0)[0]
print("magic: %08x" % magic, "(dtbo expect d7b7ab1e)")
if magic == 0xd7b7ab1e:
    totalsize, hdr_size, entry_cnt = struct.unpack_from(">III", data, 4)
    print(f"entries: {entry_cnt}")
    # dt_table_entry: dt_size, dt_offset, id, rev, custom[4]  (8*4=32 bytes each)
    off = hdr_size
    for n in range(entry_cnt):
        sz, doff, did, rev, c0, c1, c2, c3 = struct.unpack_from(">8I", data, off)
        off += 32
        m = struct.unpack_from(">I", data, doff)[0]
        print(f"  [{n}] size={sz} off={doff} id={did:#x} rev={rev} magic={m:08x} custom={c0:#x},{c1:#x},{c2:#x},{c3:#x}")
else:
    # maybe raw concatenated FDTs
    starts = []
    i = 0
    while len(starts) < 40:
        i = data.find(bytes.fromhex("d00dfeed"), i)
        if i < 0: break
        starts.append(i); i += 4
    print("raw FDT count:", len(starts), starts[:10])
