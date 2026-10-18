"""Мінімальне читання й запис Unity SerializedFile (формати 19–22, Unity 2019–2022) без сторонніх бібліотек.
Уміє лише одне: замінити дані одного об'єкта, зсунувши наступні об'єкти й оновивши таблицю."""
import struct


class SerializedFile:
    def __init__(self, data):
        self.b = bytearray(data)
        self.meta_size, self.file_size, self.version, self.data_offset = struct.unpack_from(">IIII", self.b, 0)
        if self.version not in (19, 20, 21, 22):
            raise ValueError(f"непідтримувана версія файлу: {self.version}")
        big = self.b[16] != 0
        self.e = ">" if big else "<"
        p = 20
        if self.version >= 22:                   # 64-бітні розмір і зсув даних
            self.meta_size, self.file_size, self.data_offset = struct.unpack_from(">IQQ", self.b, p); p += 28
        end = self.b.index(0, p); self.unity = self.b[p:end].decode(); p = end + 1
        p += 4                                   # платформа
        typetree = self.b[p]; p += 1
        if typetree:
            raise ValueError("файл із typetree не підтримується")
        ntypes, = struct.unpack_from(self.e + "i", self.b, p); p += 4
        for _ in range(ntypes):
            cls, = struct.unpack_from(self.e + "i", self.b, p); p += 4
            p += 1                               # isStrippedType
            sidx, = struct.unpack_from(self.e + "h", self.b, p); p += 2
            if cls == 114 or sidx >= 0: p += 16  # scriptID
            p += 16                              # oldTypeHash
        nobj, = struct.unpack_from(self.e + "i", self.b, p); p += 4
        self.objects = []                        # [path_id, start, size, type, table_offset]
        self.ofmt = self.e + ("qQIi" if self.version >= 22 else "qIIi")
        self.size_at = struct.calcsize(self.ofmt) - 8   # зсув поля size у записі таблиці
        for _ in range(nobj):
            p += -p % 4
            pid, start, size, tid = struct.unpack_from(self.ofmt, self.b, p)
            self.objects.append([pid, start, size, tid, p]); p += struct.calcsize(self.ofmt)

    def raw(self, obj):
        a = self.data_offset + obj[1]
        return bytes(self.b[a:a + obj[2]])

    def replace(self, obj, new):
        start, size = obj[1], obj[2]
        later = [o for o in self.objects if o[1] > start]
        nxt = min((o[1] for o in later), default=None)
        a = self.data_offset + start
        if nxt is None:
            tail = b""; delta = 0
            self.b[a:] = new
        else:
            new_next = start + len(new); new_next += -new_next % 8
            delta = new_next - nxt
            tail = self.b[self.data_offset + nxt:]
            self.b[a:] = new + b"\x00" * (new_next - start - len(new)) + tail
            for o in later:
                o[1] += delta
                struct.pack_into(self.e + ("Q" if self.version >= 22 else "I"), self.b, o[4] + 8, o[1])
        obj[2] = len(new)
        struct.pack_into(self.e + "I", self.b, obj[4] + self.size_at, obj[2])
        self.file_size = len(self.b)
        if self.version >= 22:
            struct.pack_into(">Q", self.b, 24, self.file_size)
        else:
            struct.pack_into(">I", self.b, 4, self.file_size)

    def bytes(self):
        return bytes(self.b)
