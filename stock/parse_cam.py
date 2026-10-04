import struct, json

def parse_fdt(buf, off):
    (magic, totalsize, off_struct, off_strings, off_rsv, ver, compat,
     boot_cpuid, sz_strings, sz_struct) = struct.unpack_from(">10I", buf, off)
    if magic != 0xd00dfeed: return None
    strings = buf[off+off_strings : off+off_strings+sz_strings]
    def getstr(o):
        e = strings.find(b"\x00", o)
        return strings[o:e].decode("utf-8", "replace") if 0 <= o < len(strings) else f"<bad:{o}>"
    pos = off + off_struct
    end = off + off_struct + sz_struct
    path = []
    tree = {}
    stack = [tree]
    while pos < end:
        tok = struct.unpack_from(">I", buf, pos)[0]; pos += 4
        if tok == 1:
            e = buf.find(b"\x00", pos)
            name = buf[pos:e].decode("utf-8", "replace")
            pos = (e + 4) & ~3
            node = {}
            path.append(name)
            key = name if name else "/"
            stack[-1].setdefault(key, {})
            node = stack[-1][key]
            stack.append(node)
        elif tok == 2:
            stack.pop()
            if path: path.pop()
        elif tok == 3:
            ln, noff = struct.unpack_from(">II", buf, pos); pos += 8
            val = buf[pos:pos+ln]
            pos = (pos + ln + 3) & ~3
            pname = getstr(noff)
            if all(32 <= b < 127 or b == 0 for b in val):
                v = val.replace(b"\x00", b"|").decode("utf-8", "replace").strip("|")
            else:
                v = "hex:" + val.hex()
            stack[-1][pname] = v
        elif tok == 9: break
    return totalsize, tree

dtb = open(r"E:\k70\stock\vendor_boot.dtb", "rb").read()
starts = []
i = 0
while True:
    i = dtb.find(bytes.fromhex("d00dfeed"), i)
    if i < 0: break
    starts.append(i); i += 4

KW = ["cam", "cci", "csi", "sensor", "actuat", "eeprom", "ov5", "ov1", "imx", "ois", "flash", "tof", "lens"]
def find_cam(node, path, out):
    for k, v in node.items():
        p = path + "/" + k
        if isinstance(v, dict):
            compat = v.get("compatible", "")
            if any(x in k.lower() or (isinstance(compat,str) and x in compat.lower()) for x in KW):
                out.append((p, compat))
            find_cam(v, p, out)

all_out = {}
for idx, s in enumerate(starts):
    r = parse_fdt(dtb, s)
    if not r: continue
    totalsize, tree = r
    out = []
    find_cam(tree, "", out)
    all_out[idx] = {"size": totalsize, "cam": out}
    print(f"=== FDT[{idx}] size={totalsize} cam-nodes={len(out)} ===")
    for p, cp in out[:25]:
        print(f"  {p}  [{cp[:90]}]")

json.dump(all_out, open(r"E:\k70\stock\cam_nodes.json", "w"), indent=1, default=str)
