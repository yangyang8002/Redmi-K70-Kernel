import struct
dtb = open(r"E:\k70\stock\vendor_boot.dtb", "rb").read()
off = 0
magic, totalsize, off_struct, off_strings, off_rsv, ver, compat, sz_strings, sz_struct = struct.unpack_from(">9I", dtb, off)
print(f"totalsize={totalsize} off_struct={off_struct} off_strings={off_strings} sz_strings={sz_strings} sz_struct={sz_struct} ver={ver}")
strings = dtb[off+off_strings : off+off_strings+sz_strings]
print("strings head:", strings[:80])
pos = off + off_struct
count = 0
while pos < off + off_struct + sz_struct and count < 15:
    tok = struct.unpack_from(">I", dtb, pos)[0]; pos += 4
    if tok == 1:
        e = dtb.find(b"\x00", pos)
        print(f"NODE '{dtb[pos:e].decode('utf-8','replace')}'")
        pos = (e + 4) & ~3
    elif tok == 2:
        print("END"); 
    elif tok == 3:
        ln, noff = struct.unpack_from(">II", dtb, pos); pos += 8
        e2 = strings.find(b"\x00", noff)
        pname = strings[noff:e2].decode("utf-8", "replace") if 0 <= noff < len(strings) else f"<bad:{noff}>"
        print(f"  PROP {pname} len={ln}")
        pos = (pos + ln + 3) & ~3
        count += 1
    elif tok == 9:
        print("FDT_END"); break
    else:
        print(f"  NOP/unknown tok={tok} at {pos-4}")
