import struct
p = r"E:\k70\stock\vermeer_images_OS3.0.307.0.WNKCNXM_16.0\images\vendor_boot.img"
out = r"E:\k70\stock\vendor_boot.dtb"
with open(p, "rb") as f:
    hdr = f.read(2128)
    ver, page = struct.unpack_from("<II", hdr, 8)
    ramdisk_size = struct.unpack_from("<I", hdr, 24)[0]
    header_size = struct.unpack_from("<I", hdr, 2096)[0]
    dtb_size = struct.unpack_from("<I", hdr, 2100)[0]
    table_size = struct.unpack_from("<I", hdr, 2112)[0]
    print(f"ver={ver} page={page} ramdisk={ramdisk_size} hdr={header_size} dtb={dtb_size} table={table_size}")
    def pages(n): return (n + page - 1) // page
    off_dtb = (pages(header_size) + pages(ramdisk_size)) * page
    print("dtb offset:", off_dtb)
    f.seek(off_dtb)
    dtb = f.read(dtb_size)
    print("dtb magic:", dtb[0:4].hex(), "(expect d00dfeed)")
    if dtb[0:4] != bytes.fromhex("d00dfeed"):
        idx = dtb.find(bytes.fromhex("d00dfeed"))
        print("first d00dfeed at:", idx)
    else:
        with open(out, "wb") as o: o.write(dtb)
        print("saved:", out, len(dtb), "bytes")
