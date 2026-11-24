import struct
import math

def _read_varint(data, pos):
    result = 0
    shift = 0
    while True:
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, pos

def _zigzag_decode(v):
    return (v >> 1) ^ -(v & 1)

def decodificar_posicao(payload: bytes):
    try:
        pos = 0
        candidatos = []
        while pos < len(payload):
            tag, pos = _read_varint(payload, pos)
            fn = tag >> 3
            wt = tag & 7
            if wt == 2:
                ln, pos = _read_varint(payload, pos)
                sub = payload[pos:pos + ln]
                pos += ln
                nome, valores = _parse_transformada(sub)
                if nome and valores.get("x") is not None:
                    candidatos.append((nome, valores))
            elif wt == 1: pos += 8
            elif wt == 5: pos += 4
            elif wt == 0: _, pos = _read_varint(payload, pos)
            else: break
        for pref in ["usv_xy_3d_id", "usv_enu_3d_id"]:
            for nome, vals in candidatos:
                if nome == pref:
                    return {"x": vals.get("x"), "y": vals.get("y"), "qw": vals.get("qw", 1.0)}
        return None
    except Exception: return None

def _parse_transformada(data: bytes):
    pos = 0; nome = None; valores = {}
    while pos < len(data):
        tag, pos = _read_varint(data, pos)
        fn = tag >> 3; wt = tag & 7
        if wt == 2:
            ln, pos = _read_varint(data, pos)
            sub = data[pos:pos + ln]; pos += ln
            if fn == 2: nome = sub.decode("utf-8", errors="replace")
            elif fn == 4: valores.update(_parse_xyzw(sub))
        elif wt == 1: pos += 8
        elif wt == 5: pos += 4
        elif wt == 0: _, pos = _read_varint(data, pos)
        else: break
    return nome, valores

def _parse_xyzw(data: bytes):
    out = {}; pos = 0
    while pos < len(data):
        tag, pos = _read_varint(data, pos)
        fn = tag >> 3; wt = tag & 7
        if wt == 5 and pos + 4 <= len(data):
            val = struct.unpack("<f", data[pos:pos + 4])[0]
            if fn == 1: out["x"] = val
            elif fn == 2: out["y"] = val
            elif fn == 4: out["qw"] = val
            pos += 4
        elif wt == 0: _, pos = _read_varint(data, pos)
        elif wt == 2:
            ln, pos = _read_varint(data, pos); pos += ln
        else: break
    return out

def decodificar_gps(payload: bytes):
    try:
        pos = 0; lat = None; lon = None
        while pos < len(payload):
            tag, pos = _read_varint(payload, pos)
            fn = tag >> 3; wt = tag & 7
            if wt == 2:
                ln, pos = _read_varint(payload, pos)
                sub = payload[pos:pos + ln]; pos += ln
                if fn == 6:
                    la, lo = _parse_gps_field6(sub)
                    if la is not None: lat, lon = la, lo
            elif wt == 0: _, pos = _read_varint(payload, pos)
            elif wt == 5: pos += 4
            elif wt == 1: pos += 8
            else: break
        if lat and lon: return {"lat": lat, "lon": lon}
        return None
    except Exception: return None

def _parse_gps_field6(data: bytes):
    pos = 0
    while pos < len(data):
        tag, pos = _read_varint(data, pos)
        fn = tag >> 3; wt = tag & 7
        if wt == 2:
            ln, pos = _read_varint(data, pos)
            sub = data[pos:pos + ln]; pos += ln
            if fn == 1:
                lon_raw, lat_raw = _parse_gps_inner(sub)
                if lon_raw is not None and lat_raw is not None:
                    return (_zigzag_decode(lat_raw) / 1e7, _zigzag_decode(lon_raw) / 1e7)
        elif wt == 0: _, pos = _read_varint(data, pos)
        elif wt == 5: pos += 4
        elif wt == 1: pos += 8
        else: break
    return None, None

def _parse_gps_inner(data: bytes):
    lon_raw = None; lat_raw = None; pos = 0
    while pos < len(data):
        tag, pos = _read_varint(data, pos)
        fn = tag >> 3; wt = tag & 7
        if wt == 0:
            v, pos = _read_varint(data, pos)
            if fn == 1: lon_raw = v
            elif fn == 2: lat_raw = v
        elif wt == 2:
            ln, pos = _read_varint(data, pos); pos += ln
        elif wt == 5: pos += 4
        elif wt == 1: pos += 8
        else: break
    return lon_raw, lat_raw

def decodificar_propulsor(payload: bytes):
    try:
        pos = 0; steer = None; modo = None
        while pos < len(payload):
            tag, pos = _read_varint(payload, pos)
            fn = tag >> 3; wt = tag & 7
            if wt == 2:
                ln, pos = _read_varint(payload, pos)
                sub = payload[pos:pos + ln]; pos += ln
                if fn == 4:
                    s, m = _parse_prop_inner(sub)
                    if s is not None: steer = s
                    if m is not None: modo = m
            elif wt == 0: _, pos = _read_varint(payload, pos)
            elif wt == 5: pos += 4
            elif wt == 1: pos += 8
            else: break
        return {"steer": steer, "modo": modo}
    except Exception: return None

def _parse_prop_inner(data: bytes):
    steer = None; modo = None; pos = 0
    while pos < len(data):
        tag, pos = _read_varint(data, pos)
        fn = tag >> 3; wt = tag & 7
        if wt == 2:
            ln, pos = _read_varint(data, pos)
            sub = data[pos:pos + ln]; pos += ln
            if fn == 3:
                p = 0
                while p < len(sub):
                    t2, p = _read_varint(sub, p)
                    f2 = t2 >> 3; w2 = t2 & 7
                    if w2 == 5 and p + 4 <= len(sub):
                        val = struct.unpack("<f", sub[p:p + 4])[0]
                        if f2 == 6: steer = val
                        elif f2 == 8: modo = val
                        p += 4
                    elif w2 == 0: _, p = _read_varint(sub, p)
                    elif w2 == 1: p += 8
                    elif w2 == 2:
                        l2, p = _read_varint(sub, p); p += l2
                    else: break
        elif wt == 0: _, pos = _read_varint(data, pos)
        elif wt == 5: pos += 4
        elif wt == 1: pos += 8
        else: break
    return steer, modo

def decodificar_radares(payload: bytes):
    try:
        pos = 0; radares = []
        while pos < len(payload):
            tag, pos = _read_varint(payload, pos)
            fn = tag >> 3; wt = tag & 7
            if wt == 2:
                ln, pos = _read_varint(payload, pos)
                sub = payload[pos:pos + ln]; pos += ln
                if fn == 5:
                    p = 0
                    while p < len(sub):
                        t2, p = _read_varint(sub, p)
                        f2 = t2 >> 3; w2 = t2 & 7
                        if w2 == 2:
                            l2, p = _read_varint(sub, p)
                            radar_data = sub[p:p + l2]; p += l2
                            if f2 == 1:
                                radar = _parse_radar(radar_data)
                                if radar: radares.append(radar)
                        elif w2 == 0: _, p = _read_varint(sub, p)
                        elif w2 == 5: p += 4
                        elif w2 == 1: p += 8
                        else: break
            elif wt == 0: _, pos = _read_varint(payload, pos)
            elif wt == 5: pos += 4
            elif wt == 1: pos += 8
            else: break
        return radares
    except Exception: return []

def _parse_radar(data: bytes):
    nome = None; x = 0.0; y = 0.0; qualidade = 0.0
    pos = 0
    while pos < len(data):
        tag, pos = _read_varint(data, pos)
        fn = tag >> 3; wt = tag & 7
        if wt == 2:
            ln, pos = _read_varint(data, pos)
            sub = data[pos:pos + ln]; pos += ln
            if fn == 2: nome = sub.decode("utf-8", errors="replace")
            elif fn == 4:
                p = 0
                while p < len(sub):
                    t2, p = _read_varint(sub, p)
                    f2 = t2 >> 3; w2 = t2 & 7
                    if w2 == 0:
                        v2, p = _read_varint(sub, p)
                        if f2 == 10: x = float(v2)
                        elif f2 == 11: y = float(v2)
                    elif w2 == 5: p += 4
                    elif w2 == 1: p += 8
                    elif w2 == 2:
                        l2, p = _read_varint(sub, p); p += l2
                    else: break
            elif fn == 6:
                p = 0
                while p < len(sub):
                    t2, p = _read_varint(sub, p)
                    f2 = t2 >> 3; w2 = t2 & 7
                    if w2 == 5 and p + 4 <= len(sub):
                        val = struct.unpack("<f", sub[p:p + 4])[0]
                        if f2 == 3: qualidade = val
                        p += 4
                    elif w2 == 0: _, p = _read_varint(sub, p)
                    else: break
        elif wt == 0: _, pos = _read_varint(data, pos)
        elif wt == 5: pos += 4
        elif wt == 1: pos += 8
        else: break
    if nome:
        dist = math.sqrt(x**2 + y**2)
        return {"nome": nome, "x": x, "y": y, "distancia": dist, "qualidade": qualidade}
    return None

def decodificar_luzes(payload: bytes):
    try:
        pos = 0; luzes = []
        while pos < len(payload):
            tag, pos = _read_varint(payload, pos)
            fn = tag >> 3; wt = tag & 7
            if wt == 2:
                ln, pos = _read_varint(payload, pos)
                sub = payload[pos:pos + ln]; pos += ln
                if fn == 5:
                    p = 0
                    while p < len(sub):
                        t2, p = _read_varint(sub, p)
                        f2 = t2 >> 3; w2 = t2 & 7
                        if w2 == 2:
                            l2, p = _read_varint(sub, p)
                            item = sub[p:p + l2]; p += l2
                            nome, status = _parse_luz(item)
                            if nome: luzes.append({"nome": nome, "status": status})
                        elif w2 == 0: _, p = _read_varint(sub, p)
                        elif w2 == 5: p += 4
                        elif w2 == 1: p += 8
                        else: break
            elif wt == 0: _, pos = _read_varint(payload, pos)
            elif wt == 5: pos += 4
            elif wt == 1: pos += 8
            else: break
        return luzes
    except Exception: return []

def _parse_luz(data: bytes):
    nome = None; status = 0; pos = 0
    while pos < len(data):
        tag, pos = _read_varint(data, pos)
        fn = tag >> 3; wt = tag & 7
        if wt == 2:
            ln, pos = _read_varint(data, pos)
            sub = data[pos:pos + ln]; pos += ln
            if fn == 3: nome = sub.decode("utf-8", errors="replace")
        elif wt == 0:
            v, pos = _read_varint(data, pos)
            if fn == 5: status = v
        elif wt == 5: pos += 4
        elif wt == 1: pos += 8
        else: break
    return nome, status

def decodificar_bateria(payload: bytes):
    try:
        pos = 0; tensao_total = 0.0; celulas = 0
        while pos < len(payload):
            tag, pos = _read_varint(payload, pos)
            fn = tag >> 3; wt = tag & 7
            if wt == 2:
                ln, pos = _read_varint(payload, pos)
                sub = payload[pos:pos + ln]; pos += ln
                p = 0
                while p < len(sub) - 3:
                    try:
                        t2, p2 = _read_varint(sub, p)
                        w2 = t2 & 7
                        if w2 == 5:
                            f = struct.unpack("<f", sub[p2:p2+4])[0]
                            if 2.0 <= f <= 4.5:
                                tensao_total += f; celulas += 1
                            p = p2 + 4
                        elif w2 == 0: _, p = _read_varint(sub, p2)
                        elif w2 == 1: p = p2 + 8
                        elif w2 == 2:
                            l2, p = _read_varint(sub, p2); p += l2
                        else: break
                    except: break
            elif wt == 0: _, pos = _read_varint(payload, pos)
            elif wt == 5: pos += 4
            elif wt == 1: pos += 8
            else: break
        if celulas > 0:
            soc = int(((tensao_total - 48.0) / (52.0 - 48.0)) * 100)
            return {"tensao": round(tensao_total, 2), "celulas": celulas, "soc": max(0, min(100, soc))}
        return None
    except Exception: return None