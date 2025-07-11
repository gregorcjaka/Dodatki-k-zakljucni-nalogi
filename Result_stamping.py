"""
Koda poljubne rezultate numericne analize pripise vozliscem objekta v Blenderju.
Skripto pozenemo v Blender 'Scripting' zavihku.
Pred zagonom spremenimo lokacijo rezultatov in ime rezultatov ter ime dodanega objekta.
"""
import bpy, csv, mathutils

txt_path = r"C:\Location\to\results.txt"         # Lokacija do .txt datoteke
object = "test_undeformed_mesh"                  # Objekt z dodanim kljucem oblike
field = "Equivalent (von-Mises) Stress (Pa)"     # Ime rezultatov
scale = 1.0                                      # Ce so enote v metrih, pustim na 1

def str2f(s): return float(s.replace(',', '.'))

# 1) Preberemo datoteko z rezultati, sestavimo mathutils vektor, shranimo napetost v nodes_val
nodes_co   = []
nodes_val  = []

with open(txt_path, encoding="utf-8", newline='') as f:
    # Spustimo vse vrstice s komentarji
    for line in f:
        if not line.startswith('#'):
            header_raw = line.rstrip('\r\n').split('\t')
            break
    header = [h.strip() for h in header_raw]
    hmap   = {h: i for i, h in enumerate(header)}
    need   = ("X", "Y", "Z", field)
    # Preverimo, da imamo vse potrebne podatke
    if not all(k in hmap for k in need):
        raise RuntimeError(f"Missing one of {need} in TXT header: {header}")

    for row in csv.reader(f, delimiter='\t'):
        if not row or len(row) < len(header):
            continue
        co = mathutils.Vector((str2f(row[hmap["X"]]) * scale,
                               str2f(row[hmap["Y"]]) * scale,
                               str2f(row[hmap["Z"]]) * scale))
        nodes_co.append(co)
        nodes_val.append(str2f(row[hmap[field]]))

# 2) Zgradimo drevo velikosti nodes_co in ga napolnimo s koordinatami vozlisc
kd = mathutils.kdtree.KDTree(len(nodes_co))
for i, co in enumerate(nodes_co):
    kd.insert(co, i)
kd.balance()        # Poskrbi, da so tocke v optimalnem uravnotezenem drevesu

# 3) Pripisemo vrednosti na verteks-barvo
obj   = bpy.data.objects[object]
mesh  = obj.data
world = obj.matrix_world          # V primeru, da transformacije niso potrjene

# Ustvarimo verteks sloj (oz. ga pridobimo, ce je ta ze ustvarjen)
layer = mesh.color_attributes.get(field) \
        or mesh.color_attributes.new(field, type='FLOAT_COLOR', domain='POINT')

# Glavna zanka
for v in mesh.vertices:
    co_world = world @ v.co
    _, idx, _ = kd.find(co_world)
    val = nodes_val[idx]
    layer.data[v.index].color = (val, val, val, 1.0)        
mesh.update()

print("Result value min:", min(nodes_val))      # Dobimo se informacijo o min in max resitvi
print("Result value max:", max(nodes_val))
print(f"Stamped stress on {len(mesh.vertices):,} of {len(mesh.vertices):,} vertices.")
