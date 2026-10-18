"""Texture2D у форматі Unity 2021.3 без typetree: розбір полів і заміна картинки на нестиснену RGBA32.
Нова картинка зберігається прямо в об'єкті, а не в .resS, тож файл .resS не змінюється."""
import struct

RGBA32 = 4


def _align(p): return p + (-p % 4)


def parse(raw):
    """Повертає словник зі зсувами потрібних полів."""
    t = {}
    n, = struct.unpack_from("<i", raw, 0)
    t["name"] = raw[4:4 + n].decode("utf-8")
    p = _align(4 + n)
    p += 4                                   # m_ForcedFallbackFormat
    p = _align(p + 2)                        # m_DownscaleFallback, m_IsAlphaChannelOptional
    t["head"] = p                            # далі: ширина, висота, розмір, mipsStripped, формат, mipCount
    t["width"], t["height"], t["size"], _, t["format"], t["mips"] = struct.unpack_from("<6i", raw, p)
    p += 24
    p = _align(p + 4)                        # m_IsReadable, m_IsPreProcessed, m_IgnoreMasterTextureLimit, m_StreamingMipmaps
    p += 4 * 3                               # m_StreamingMipmapsPriority, m_ImageCount, m_TextureDimension
    p += 4 * 6                               # m_TextureSettings
    p += 4 * 2                               # m_LightmapFormat, m_ColorSpace
    blob, = struct.unpack_from("<i", raw, p)
    p = _align(p + 4 + blob)                 # m_PlatformBlob
    t["data"] = p                            # image data: розмір + байти
    size, = struct.unpack_from("<i", raw, p)
    p = _align(p + 4 + size)
    t["stream"] = p                          # m_StreamData: offset u64, size u32, path
    t["stream_offset"], t["stream_size"], plen = struct.unpack_from("<QIi", raw, p)
    t["stream_path"] = raw[p + 16:p + 16 + plen].decode("utf-8")
    end = _align(p + 16 + plen)
    if end != len(raw):
        raise ValueError(f"Texture2D {t['name']}: незнайома структура ({end} ≠ {len(raw)})")
    return t


def replace_image(raw, width, height, mips, pixels):
    """Новий об'єкт: та сама текстура, але RGBA32 з mip-рівнями, дані всередині об'єкта."""
    t = parse(raw)
    if (t["width"], t["height"]) != (width, height):
        raise ValueError(f"{t['name']}: розмір {t['width']}×{t['height']}, а картинка {width}×{height}")
    head = bytearray(raw[:t["data"]])
    struct.pack_into("<6i", head, t["head"], width, height, len(pixels), 0, RGBA32, mips)
    body = struct.pack("<i", len(pixels)) + pixels
    body += b"\x00" * (-len(body) % 4)
    stream = struct.pack("<QIi", 0, 0, 0)
    return bytes(head) + body + stream
