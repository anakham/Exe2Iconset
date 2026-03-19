import pefile
import struct

def get_entry_name(entry, level):
    if level == 0:
        return pefile.RESOURCE_TYPE.get(entry.id, f"TYPE_{entry.id}")
    elif hasattr(entry, 'name') and entry.name:
        return entry.name
    else:
        return f"ID_{entry.id}"

def print_data_entry(pe, entry, indent):
    if hasattr(entry, 'data') and entry.data:
        offset = entry.data.struct.OffsetToData
        size = entry.data.struct.Size
        data = pe.get_memory_mapped_image()[offset:offset+size]
        print(f"{indent}Data: offset={offset}, size={size}, bytes={len(data)}")
        return data
    return None

def parse_group_icon(pe, data, indent):
    if len(data) >= 6:
        idReserved, idType, idCount = struct.unpack('<HHH', data[:6])
        print(f"{indent}Group descriptor: type={idType}, count={idCount}")
        offset = 6
        for i in range(idCount):
            if offset + 14 > len(data):
                break
            bWidth, bHeight, bColorCount, bReserved, wPlanes, wBitCount, dwBytesInRes, nID = struct.unpack('<BBBBHHIH', data[offset:offset+14])
            w = bWidth if bWidth else 256
            h = bHeight if bHeight else 256
            print(f"{indent}  Icon entry: {w}x{h}, resource_id={nID}, size={dwBytesInRes}")
            offset += 14

def print_resource_hierarchy(pe, level=0, type_entry=None, res_name=""):
    indent = "  " * level
    
    if level == 0:
        if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
            print("No resource directory")
            return
        print("=== Resource Directory Root ===")
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            name = get_entry_name(entry, level)
            print(f"{indent}Type: {name} (id={entry.id})")
            if hasattr(entry, 'directory') and entry.directory:
                print_resource_hierarchy(pe, level + 1, entry, name)
    
    elif level == 1:
        name = get_entry_name(type_entry, level)
        print(f"{indent}Resource: {name}")
        
        if hasattr(type_entry, 'directory') and type_entry.directory:
            for id_entry in type_entry.directory.entries:
                res_id_name = get_entry_name(id_entry, level)
                print(f"{indent}  ID/Name: {res_id_name}")
                
                if hasattr(id_entry, 'directory') and id_entry.directory:
                    for lang_entry in id_entry.directory.entries:
                        lang_id = lang_entry.id if hasattr(lang_entry, 'id') and lang_entry.id else 0
                        primary_lang = pefile.LANG.get(lang_id & 0x3FF, f"LANG_{lang_id & 0x3FF}")
                        print(f"{indent}    Language: {primary_lang}/0x{lang_id:04X}")
                        
                        data = print_data_entry(pe, lang_entry, indent + "      ")
                        if data and 'RT_GROUP_ICON' in res_name:
                            parse_group_icon(pe, data, indent + "      ")
                else:
                    data = print_data_entry(pe, id_entry, indent + "    ")
                    if data and 'RT_GROUP_ICON' in res_name:
                        parse_group_icon(pe, data, indent + "    ")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file1> [file2] ...")
        return
    
    paths = sys.argv[1:]
    
    for path in paths:
        print(f"\n{'='*60}")
        print(f"File: {path}")
        print('='*60)
        try:
            pe = pefile.PE(path)
            print_resource_hierarchy(pe)
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    main()
