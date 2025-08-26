import ezdxf
import os

def process_dxf(input_path, output_path, tolerance):
    """
    Reads a DXF file, converts curve entities (SPLINE, POLYLINE, LWPOLYLINE)
    into a series of LINE entities, and saves the result to a new file.
    Returns logs of the process.
    """
    logs = []
    try:
        logs.append(f"Reading file: {os.path.basename(input_path)}...")
        doc = ezdxf.readfile(input_path)
        msp = doc.modelspace()
    except IOError:
        logs.append(f"Error: Cannot find or open file '{input_path}'")
        return False, "File not found.", logs
    except ezdxf.DXFStructureError as e:
        logs.append(f"Error: Invalid or corrupt DXF file. Message: {e}")
        return False, "Invalid DXF file.", logs
    except Exception as e:
        logs.append(f"An unexpected error occurred while reading the file: {e}")
        return False, "Error reading file.", logs

    entities_to_convert = msp.query("SPLINE POLYLINE LWPOLYLINE")
    logs.append(f"Found {len(entities_to_convert)} entities to process.")
    if not entities_to_convert:
        return True, "No entities needed conversion.", logs

    entities_processed_count = 0
    for entity in list(entities_to_convert):
        if not entity.is_alive:
            continue
        try:
            if entity.dxftype() == 'SPLINE':
                points = list(entity.flattening(distance=tolerance))
                if len(points) > 1:
                    logs.append(f"  - Converting SPLINE (handle: {entity.dxf.handle}) to {len(points) - 1} LINE segments.")
                    safe_attribs = {
                        'layer': entity.dxf.get('layer', '0'),
                        'color': entity.dxf.get('color', 256),
                        'linetype': entity.dxf.get('linetype', 'BYLAYER'),
                        'lineweight': entity.dxf.get('lineweight', -1),
                    }
                    for i in range(len(points) - 1):
                        msp.add_line(start=points[i], end=points[i+1], dxfattribs=safe_attribs)
                    msp.delete_entity(entity)
                    entities_processed_count += 1
            elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
                logs.append(f"  - Exploding {entity.dxftype()} (handle: {entity.dxf.handle}).")
                entity.explode()
                entities_processed_count += 1
        except Exception as e:
            logs.append(f"  - FAILED to process entity {entity.dxftype()} (handle: {entity.dxf.handle}). Error: {e}")

    if entities_processed_count > 0:
        logs.append(f"\nTotal of {entities_processed_count} original entities were processed.")
        logs.append(f"Saving result to new file: {os.path.basename(output_path)}")
        try:
            doc.saveas(output_path)
            logs.append("\nDONE! New file created successfully.")
            return True, "Conversion successful!", logs
        except Exception as e:
            logs.append(f"Failed to save file. Error: {e}")
            return False, "Failed to save file.", logs
    else:
        logs.append("\nNo entities were successfully converted. No new file was saved.")
        return True, "No entities were converted.", logs

if __name__ == "__main__":
    print("--- Curve to Line Conversion Script v3.1 ---")
    input_file = input("Enter the source DXF file name: ")
    tolerance_val = float(input("Enter the tolerance for SPLINE conversion (e.g., 0.01): "))
    output_file = f"{os.path.splitext(input_file)[0]}_converted.dxf"
    
    success, message, logs = process_dxf(input_file, output_file, tolerance_val)
    
    print("\n--- LOGS ---")
    for log in logs:
        print(log)
    print(f"\nResult: {message}")
