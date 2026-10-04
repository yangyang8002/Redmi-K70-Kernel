import struct

dtb = open(r"E:\k70\stock\vendor_boot.dtb", "rb").read()
# find all FDT starts
starts = []
i = 0
while True:
    i = dtb.find(bytes.fromhex("d00dfeed"), i)
    if i < 0: break
    starts.append(i); i += 4
print("FDT count:", len(starts))

def parse_fdt(buf, off):
    magic, totalsize, off_struct, off_strings, off_rsv, ver, compat, sz_strings, sz_struct = struct.unpack_from(">9I", buf, off)
    if magic != 0xd00dfeed: return None
    strings = buf[off+off_strings : off+off_strings+sz_strings]
    def getstr(o):
        e = strings.find(b"\x00", o)
        return strings[o:e].decode("utf-8", "replace")
    pos = off + off_struct
    end = off + off_struct + sz_struct
    nodes = []
    path = []
    props = []
    while pos < end:
        tok = struct.unpack_from(">I", buf, pos)[0]; pos += 4
        if tok == 1:  # BEGIN_NODE
            e = buf.find(b"\x00", pos)
            name = buf[pos:e].decode("utf-8", "replace")
            pos = (e + 4) & ~3
            path.append(name)
            nodes.append(("/" + "/".join(path)).replace("//", "/"))
        elif tok == 2:  # END_NODE
            if path: path.pop()
        elif tok == 3:  # PROP
            ln, noff = struct.unpack_from(">II", buf, pos); pos += 8
            val = buf[pos:pos+ln]
            pos = (pos + ln + 3) & ~3
            pname = getstr(noff)
            full = ("/" + "/".join(path)).replace("//", "/")
            if pname == "compatible":
                props.append((full, val.replace(b"\x00", b"|").decode("utf-8", "replace").strip("|")))
        elif tok == 9: break
    return totalsize, nodes, props

# parse each FDT, look for camera keywords
for idx, s in enumerate(starts):
    try:
        r = parse_fdt(dtb, s)
    except Exception as ex:
        print(f"[{idx}] parse fail at {s}: {ex}"); continue
    if not r: continue
    totalsize, nodes, props = r
    cam_nodes = [n for n in nodes if any(k in n.lower() for k in ["cam", "cci", "csi", "sensor", "actuator", "eeprom", "ov50", "imx"])]
    model = [p[1] for p in props if p[0] == "/"]
    print(f"[{idx}] off={s} size={totalsize} nodes={len(nodes)} root-compat={model[:2]} cam-nodes={len(cam_nodes)}")
