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
    flat = {}   # path -> {prop: val}
    path = []
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
            if all(32 <= b < 127 or b == 0 for b in val):
                v = val.replace(b"\x00", b"|").decode("utf-8", "replace").strip("|")
            else:
                v = "hex:" + val.hex()
            flat.setdefault(full, {})[pname] = v
        elif tok == 9: break
    return totalsize, flat

dtb = open(r"E:\k70\stock\vendor_boot.dtb", "rb").read()
starts = []
i = 0
while True:
    i = dtb.find(bytes.fromhex("d00dfeed"), i)
    if i < 0: break
    starts.append(i); i += 4

KW = ["cam_sensor", "cam-sensor", "qcom,cam", "cci", "actuator", "eeprom", "ois", "ov5", "ov1", "imx", "s5k", "gc5", "hi8", "flash", "csiphy", "tof"]
result = {}
for idx, s in enumerate(starts):
    r = parse_fdt(dtb, s)
    if not r: continue
    totalsize, flat = r
    hits = []
    for p, props in flat.items():
        cp = props.get("compatible", "")
        if any(k in p.lower() or k in cp.lower() for k in KW):
            hits.append((p, cp))
    result[idx] = hits
    print(f"=== FDT[{idx}] nodes={len(flat)} cam-hits={len(hits)} ===")
    for p, cp in hits[:30]:
        print(f"  {p}  [{cp[:95]}]")

json.dump(result, open(r"E:\k70\stock\cam_nodes.json","w"), indent=1)
