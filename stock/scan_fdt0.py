import struct

def parse_fdt(buf, off):
    magic, totalsize, off_struct, off_strings, off_rsv, ver, compat, sz_strings, sz_struct = struct.unpack_from(">9I", buf, off)
    if magic != 0xd00dfeed: return None
    strings = buf[off+off_strings : off+off_strings+sz_strings]
    def getstr(o):
        e = strings.find(b"\x00", o)
        return strings[o:e].decode("utf-8", "replace")
    pos = off + off_struct
    end = off + off_struct + sz_struct
    path = []
    entries = []
    while pos < end:
        tok = struct.unpack_from(">I", buf, pos)[0]; pos += 4
        if tok == 1:
            e = buf.find(b"\x00", pos)
            name = buf[pos:e].decode("utf-8", "replace")
            pos = (e + 4) & ~3
            path.append(name)
        elif tok == 2:
            if path: path.pop()
        elif tok == 3:
            ln, noff = struct.unpack_from(">II", buf, pos); pos += 8
            val = buf[pos:pos+ln]
            pos = (pos + ln + 3) & ~3
            pname = getstr(noff)
            full = "/" + "/".join(path)
            if pname == "compatible":
                cs = val.replace(b"\x00", b"|").decode("utf-8", "replace").strip("|")
                entries.append((full, cs))
        elif tok == 9: break
    return entries

dtb = open(r"E:\k70\stock\vendor_boot.dtb", "rb").read()
e0 = parse_fdt(dtb, 0)
print("=== FDT[0] camera-related compatibles ===")
for path, cs in e0:
    if any(k in path.lower() or k in cs.lower() for k in ["cam", "cci", "csi", "sensor", "actuat", "eeprom", "ov5", "imx", "ois", "flash"]):
        print(f"  {path}\n      -> {cs[:100]}")
print()
print("=== FDT[0] all root-level fragments (first 20) ===")
seen = set()
for path, cs in e0:
    top = "/".join(path.split("/")[:3])
    if top not in seen:
        seen.add(top)
        print("  " + top)
