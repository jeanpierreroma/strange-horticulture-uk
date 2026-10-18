"""Читання бінарного формату серіалізації Odin (Sirenix), яким гра зберігає TranslationData."""
import struct
NAMED={1,3,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,50}
FIX={15:1,16:1,17:1,18:1,19:2,20:2,21:2,22:2,23:4,24:4,25:4,26:4,27:8,28:8,29:8,30:8,31:4,32:4,33:8,34:8,35:16,36:16,37:2,38:2,41:16,42:16,43:1,44:1,9:4,10:4,11:4,12:4,13:16,14:16}
class R:
    def __init__(s,b): s.b=b; s.p=0
    def u8(s): v=s.b[s.p]; s.p+=1; return v
    def i32(s): v=struct.unpack_from('<i',s.b,s.p)[0]; s.p+=4; return v
    def str_(s):
        f=s.u8(); n=s.i32()
        if f==0: v=s.b[s.p:s.p+n].decode('latin-1'); s.p+=n
        else: v=s.b[s.p:s.p+2*n].decode('utf-16-le','surrogatepass'); s.p+=2*n
        return v
def parse(b):
    """Токени: [тип запису, ім'я, значення, початок, кінець, початок рядка-значення]"""
    r=R(b); toks=[]
    while r.p<len(b):
        st=r.p; e=r.u8(); name=None; val=None; vs=None
        if e in NAMED: name=r.str_()
        if e in (1,2,3,4):
            te=r.u8()
            if te==47: tid=r.i32(); tn=r.str_(); val=('typename',tid,tn)
            elif te==48: val=('typeid',r.i32())
            elif te==46: val=('nulltype',)
            else: raise Exception(f'bad type entry {te} at {r.p}')
            if e in (1,2): val=val+(r.i32(),)
        elif e in (5,7,49): pass
        elif e==6: val=struct.unpack_from('<q',b,r.p)[0]; r.p+=8
        elif e==8: n=r.i32(); sz=r.i32(); r.p+=n*sz
        elif e in (39,40,50,51): vs=r.p; val=r.str_()
        elif e in FIX: r.p+=FIX[e]
        elif e in (45,46): pass
        else: raise Exception(f'unknown entry {e} at {st}')
        toks.append([e,name,val,st,r.p,vs])
        if e==49: break
    return toks, r.p
def wstr(s):
    return b'\x01'+struct.pack('<i',len(s.encode('utf-16-le','surrogatepass'))//2)+s.encode('utf-16-le','surrogatepass')
