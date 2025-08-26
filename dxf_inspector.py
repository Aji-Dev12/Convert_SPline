import ezdxf
from collections import Counter
import os

def inspect_dxf(filename):
    """
    Membaca file DXF dan melaporkan ringkasan entitas di dalamnya.
    """
    # Memastikan path file lengkap jika file ada di direktori yang sama
    if not os.path.isabs(filename):
        filename = os.path.join(os.getcwd(), filename)

    try:
        print(f"Membaca file: {filename}...")
        doc = ezdxf.readfile(filename)
        msp = doc.modelspace()
    except IOError:
        print(f"Error: Tidak dapat menemukan atau membuka file '{filename}'")
        return
    except ezdxf.DXFStructureError as e:
        print(f"Error: File '{filename}' bukan file DXF yang valid atau rusak. Pesan: {e}")
        return
    except Exception as e:
        print(f"Terjadi error yang tidak terduga: {e}")
        return

    print("\n--- Laporan Inspeksi DXF ---")
    print(f"File: {os.path.basename(filename)}")
    
    if not msp:
        print("Modelspace kosong atau tidak ditemukan.")
        return

    all_entities = list(msp)
    
    if not all_entities:
        print("Modelspace tidak berisi entitas apapun.")
        return

    # Hitung semua jenis entitas
    entity_counts = Counter(entity.dxftype() for entity in all_entities)

    print(f"Total entitas ditemukan di modelspace: {len(all_entities)}")
    print("----------------------------------------")
    print("Rincian per jenis entitas:")
    for entity_type, count in sorted(entity_counts.items()):
        print(f"- {entity_type}: {count} buah")
    print("----------------------------------------")

    # Periksa keberadaan entitas yang bisa dikonversi
    entities_to_convert = ["SPLINE", "POLYLINE", "LWPOLYLINE"]
    found_convertible = False
    print("Pemeriksaan untuk skrip konversi:")
    for entity_type in entities_to_convert:
        if entity_counts[entity_type] > 0:
            print(f"[OK] Ditemukan {entity_counts[entity_type]} buah {entity_type}. Entitas ini BISA diproses.")
            found_convertible = True
    
    if not found_convertible:
        print("[INFO] Tidak ditemukan entitas SPLINE, POLYLINE, atau LWPOLYLINE.")
        print("Ini adalah alasan mengapa skrip convert_to_lines.py tidak membuat file output.")

    print("\n--- Akhir Laporan ---")

if __name__ == "__main__":
    print("--- Skrip Inspektur File DXF v1.0 ---")
    input_file = ""
    while not input_file:
        input_file = input("Masukkan nama file DXF yang ingin diperiksa: ")
    inspect_dxf(input_file)
