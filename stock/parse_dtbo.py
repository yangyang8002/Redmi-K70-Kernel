import struct, json

def parse_fdt(buf, off):
    try:
        (magic, totalsize, off_struct, off_strings, off_rsv, ver, compat,
         boot_cpuid, sz_strings, sz_struct) = struct.unpack_from(">10I", buf, off)
        if magic != 0xd00dfeed: return None
        strings = buf[off+off_strings : off+off_strings+sz_strings]
        def getstr(o):
            e = strings.find(b"\x00", o)
            return strings[o:e].decode("utf-8", "replace") if 0 <= o < len(strings) else ""
        pos = off + off_struct
        end = off + off_struct + sz_struct
        flat = {}
        path = []
        guard = 0
        while pos < end and guard < 200000:
            guard += 1
            tok = struct.unpack_from(">I", buf, pos)[0]; pos += 4
            if tok == 1:
                e = buf.find(b"\x00", pos)
                path.append(buf[pos:e].decode("utf-8", "replace"))
                pos = (e + 4) & ~3
            elif tok == 2:
                if path: path.pop()
            elif tok == 3:
                ln, noff = struct.unpack_from(">II", buf, pos); pos += 8
                val = buf[pos:pos+ln]
                pos = (pos + ln + 3) & ~3
                full = "/" + "/".join(path)
                if all(32 <= b < 127 or b == 0 for b in val):
                    v = val.replace(b"\x00", b"|").decode("utf-8", "replace").strip("|")
                else:
                    v = "hex:" + val.hex()
                flat.setdefault(full, {})[getstr(noff)] = v
            elif tok == 9: break
        return totalsize, flat
    except Exception:
        return None

data = open(r"E:\k70\stock\vermeer_images_OS3.0.307.0.WNKCNXM_16.0\images\dtbo.img", "rb").read()
entry_cnt = struct.unpack_from(">I", data, 12)[0]
hdr_size = struct.unpack_from(">I", data, 8)[0]
KW = ["cam-sensor", "cam_sensor", "qcom,cam", "actuator", "eeprom", "ois", "ov5", "ov1", "imx", "s5k", "gc5", "hi8", "flash", "csiphy", "tof", "lens", "vermeer"]
off = hdr_size
summary = {}
for n in range(entry_cnt):
    sz, doff = struct.unpack_from(">II", data, off)
    off += 32
    r = parse_fdt(data, doff)
    if not r: continue
    totalsize, flat = r
    hits = [(p, pr.get("compatible","")) for p, pr in flat.items()
            if any(k in p.lower() or k in pr.get("compatible","").lower() for k in KW)]
    # also root compatible to identify which device
    rootc = flat.get("/", {}).get("compatible", "")
    summary[n] = {"nodes": len(flat), "root": rootc, "hits": len(hits)}
    if hits:
        print(f"=== entry[{n}] nodes={len(flat)} root={rootc[:80]} hits={len(hits)} ===")
        for p, cp in hits[:20]:
            print(f"  {p}  [{cp[:85]}]")
json.dump(summary, open(r"E:\k70\stock\dtbo_summary.json","w"), indent=1)
print()
print("=== all entries overview ===")
for n, s in summary.items():
    print(f"  [{n}] nodes={s['nodes']} hits={s['hits']} root={s['root'][:70]}")
