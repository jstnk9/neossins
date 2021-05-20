# This script was modified in order to properly work with neossins
# Original script: https://github.com/cylance/GetNETGUIDs
# Original author: Brian Wallace (@botnet_hunter)

import pefile
import struct
import re
import datetime

guid_regex = re.compile(b"[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}")


def format_guid_from_hex(hex_string):
    first = hex_string[6:8] + hex_string[4:6] + hex_string[2:4] + hex_string[:2]
    second = hex_string[10:12] + hex_string[8:10]
    third = hex_string[14:16] + hex_string[12:14]
    return "{0}-{1}-{2}-{3}-{4}".format(first, second, third, hex_string[16:20], hex_string[20:])


def read_blob(blob):
    if len(blob) == 0:
        return ""
    first_byte = blob[0]
    if first_byte & 0x80 == 0:
        # easy one
        raw_string = blob[1:][:first_byte]
        length_determined_string = raw_string[2:][:-2]
        if len(length_determined_string) != 0:
            return length_determined_string[1:]
        return length_determined_string
    # Our string is not very long
    return ""


def is_dot_net_assembly(pe):
    return pe.OPTIONAL_HEADER.DATA_DIRECTORY[14].VirtualAddress != 0

def get_compiletime(pe):
        return datetime.datetime.fromtimestamp(pe.FILE_HEADER.TimeDateStamp)

def get_assembly_guids(assembly_path):
    try:
        try:
            pe = pefile.PE(assembly_path)

            txt_start = None
            txt_end = None
            for section in pe.sections:
                if section.Name.startswith(b".text\x00"):
                    txt_start = section.PointerToRawData
                    txt_end = txt_start + section.SizeOfRawData
        except pefile.PEFormatError:
            return b""
        if not is_dot_net_assembly(pe):
            return b""
            
        #Compile TimeDateStamp
        try:
            compiled = get_compiletime(pe)
        except Exception:
            compiled = "Error"

        # Removed strict parsing and opted for simple searching method to support malformed assemblies
        with open(assembly_path, "rb") as assembly_file_handler:
            file_data = assembly_file_handler.read()

        text_section = file_data[txt_start:][:txt_end]


        mdo = pe.get_offset_from_rva(struct.unpack("<IHHI", text_section[8:][:12])[-1])

        if mdo < txt_start:
            offsets_to_test = [mdo]
        else:
            offsets_to_test = [mdo - txt_start]

        offsets_to_test.extend([l.start() for l in re.finditer(b"\x42\x53\x4a\x42", text_section)][::-1])

        del file_data

        for i_offset in offsets_to_test:
            i = text_section[i_offset:]
            try:
                if b"\x42\x53\x4a\x42" not in i:
                    continue
                if not i.startswith(b"\x42\x53\x4a\x42"):
                    continue
                meta_data_offset = i.find(b"\x42\x53\x4a\x42")
                clr_version_length = struct.unpack("<I", i[meta_data_offset + 12:meta_data_offset + 16])[0]
                try:
                    stream_count = struct.unpack("<H", i[meta_data_offset + clr_version_length +
                                                         18:meta_data_offset + clr_version_length + 20])[0]
                except struct.error:
                    continue
                current_offset = meta_data_offset + clr_version_length + 20
                heaps = {}
                for c in range(stream_count):
                    offset = struct.unpack("<I", i[current_offset:current_offset + 4])[0]
                    size = struct.unpack("<I", i[current_offset + 4:current_offset + 8])[0]
                    current_offset += 8
                    name = b""
                    while b"\x00" not in name:
                        name += i[current_offset:current_offset + 4]
                        current_offset += 4
                    name = name.strip(b"\x00")
                    # print "{0} at {1}, {2} bytes".format(name, offset, size)
                    heaps[name] = i[meta_data_offset + offset:meta_data_offset + offset + size]
                    # if len(heaps[name]) != size:
                    #    raise

                try:
                    extracted_mvid = format_guid_from_hex(heaps[b"#GUID"][:16])
                except:
                    return b""

                tilde = heaps[b"#~"]

                if tilde is not None:
                    # print "Reserved: {0}".format([tilde[0:4]])
                    # print "Major: {0}".format([tilde[4:5]])
                    # print "Minor: {0}".format([tilde[5:6]])

                    # print "Heap offset indication: {0}".format([tilde[6:7]])
                    strings_heap_index_length = 2 if ord(tilde[6:7]) & 0x01 == 0x00 else 4
                    guid_heap_index_length = 2 if ord(tilde[6:7]) & 0x02 == 0x00 else 4
                    blob_heap_index_length = 2 if ord(tilde[6:7]) & 0x04 == 0x00 else 4

                    # print "Reserved 0x01: {0}".format([tilde[7:8]])
                    # print "Table list: {0}".format([tilde[8:16]])

                    tables_present = [x == "1" for x in bin(struct.unpack("<Q", tilde[8:16])[0])[2:][::-1]]
                    # tables_present_count = len([a for a in tables_present if a])
                    # print "Tables present count: {0}".format(tables_present_count)

                    # print "Which tables are sorted list: {0}".format([tilde[16:24]])

                    row_counts = [0] * 64
                    t_offset = 24
                    for index in range(len(tables_present)):
                        if index < len(tables_present) and tables_present[index]:
                            row_counts[index] = struct.unpack("<I", tilde[t_offset:t_offset + 4])[0]
                            t_offset += 4

                    has_custom_attribute_tables = [
                        0x06, 0x04, 0x01, 0x02, 0x08, 0x09, 0x0A, 0x00,
                        0x0E, # Permission aka DeclSecurity (typo in the spec)
                        0x17, 0x14, 0x11, 0x1A, 0x1B, 0x20, 0x23, 0x26,
                        0x27, 0x2A, 0x2C, 0x2B
                    ]
                    custom_attribute_type_tables = [0x06, 0x0A]
                    resolution_scope_tables = [0x00, 0x1A, 0x23, 0x01]
                    type_def_or_ref_tables = [0x02, 0x01, 0x1B]
                    member_ref_tables = [0x02, 0x01, 0x1A, 0x06, 0x1B]

                    big_has_custom_attribute = any([row_counts[x] >= 2**(16 - 5) for x in has_custom_attribute_tables])
                    big_custom_attribute_type = any([row_counts[x] >= 2**(16 - 3) for x in custom_attribute_type_tables])
                    big_resolution_scope = any([row_counts[x] >= 2**(16 - 2) for x in resolution_scope_tables])
                    big_type_def_or_ref = any([row_counts[x] >= 2**(16 - 2) for x in type_def_or_ref_tables])
                    big_member_ref_parent = any([row_counts[x] >= 2**(16 - 3) for x in member_ref_tables])

                    # Build row length for each type up to CustomAttr
                    row_type_widths = [
                        # 0x00 Module = Generation (2 bytes) + Name (String heap index) + Mvid (Guid heap index) +
                        # EncId (Guid heap index) + EncBaseId (Guid heap index)
                        2 + strings_heap_index_length + (guid_heap_index_length * 3),

                        # 0x01 TypeRef = ResolutionScope (ResolutionScope index) + TypeName (String heap) +
                        # TypeNamespace (String heap)
                        (4 if big_resolution_scope else 2) + (strings_heap_index_length * 2),
                        # 0x02 TypeDef = Flags(2 bytes) + TypeName(String heap index) +TypeNamespace(String heap index)+
                        # Extends (TypeDefOrRef index) + FieldList (index into field table) +
                        # MethodList (index into MethodDef table) + ?
                        8 + (4 if big_type_def_or_ref else 2) + (strings_heap_index_length * 2),
                        0,  # 0x03 None
                        # 0x04 Field = Flags (2 bytes) + Name (String heap index) + Signature (Blob heap index)
                        2 + strings_heap_index_length + blob_heap_index_length,
                        0,  # 0x05 None
                        # 0x06 MethodDef = RVA(4 bytes) + ImplFlags(2 bytes) + Flags(2 bytes) + Name(String heap index)+
                        # Signature (Blob heap index) + ParamList (index to param table)
                        10 + strings_heap_index_length + blob_heap_index_length,
                        0,  # 0x07 None
                        # 0x08 Param = Flags (2 bytes) + Sequence (2 bytes) + Name (String heap index)
                        4 + strings_heap_index_length,
                        # 0x09 InterfaceImpl = Class (TypeDef index) + Interface (TypeDefOrRef index)
                        2 + (4 if big_type_def_or_ref else 2),
                        # 0x0a MemberRef = Class(MemberRefParent) + Name(String heap index) + Signature(Blob heap index)
                        (4 if big_member_ref_parent else 2) + strings_heap_index_length + blob_heap_index_length,
                        # 0x0b Constant = Type (?) + Parent + Value (Blob heap index)
                        4 + blob_heap_index_length,
                        # 0x0c CustomAttr = Parent + Type (CustomAttributeType) + Value (Blob heap index)
                        (4 if big_has_custom_attribute else 2) + (4 if big_custom_attribute_type else 2) + blob_heap_index_length,
                        # Don't care about the rest
                    ]

                    for index in range(0x0c):
                        t_offset += row_type_widths[index] * row_counts[index]

                    for index in range(row_counts[0x0c]):
                        # In the most strict interpretation, a typelib id is expressed as a
                        # GuidAttribute on the current assembly.
                        # To check that it's actually a GuidAttribute we'd have to support parsing
                        # .NET signatures, so it's safer to assume a MemberRef attribute owned by a
                        # TypeRef on an AssemblyRow with a value matching a guid is PROBABLY the typelib id

                        row_offset = t_offset

                        if big_has_custom_attribute:
                            parent_index = struct.unpack("<I", tilde[row_offset:row_offset + 4])[0]
                            row_offset += 4
                        else:
                            parent_index = struct.unpack("<H", tilde[row_offset:row_offset + 2])[0]
                            row_offset += 2

                        if big_custom_attribute_type:
                            type_index = struct.unpack("<I", tilde[row_offset:row_offset + 4])[0]
                            row_offset += 4
                        else:
                            type_index = struct.unpack("<H", tilde[row_offset:row_offset + 2])[0]
                            row_offset += 2

                        parent_index_table = parent_index & 0x1f
                        type_index_table = type_index & 0x07

                        # We only really care if the parent is an Assembly and the attribute is constructed
                        # using a MemberRef. MemberRef because a MethodDef is never going to be used for a
                        # GuidAttribute. This is because GuidAttribute is from mscorlib, so always an external
                        # assembly, so always reached via TypeRef/MemberRef.
                        if parent_index_table == 0x0e and type_index_table == 0x03:
                            if blob_heap_index_length == 2:
                                blob_index = struct.unpack("<H", tilde[row_offset:row_offset + 2])[0]
                                row_offset += 2
                            else:
                                blob_index = struct.unpack("<I", tilde[row_offset:row_offset + 4])[0]
                                row_offset += 4

                            data_value = read_blob(heaps[b"#Blob"][blob_index:])
                            if guid_regex.match(data_value):
                                return data_value.lower()
                        t_offset += row_type_widths[0x0c]
                    return b""
            except KeyboardInterrupt:
                raise
            except:
                pass
    except KeyboardInterrupt:
        raise
    except:
        return b""
    return b""


def get_netguid(file_path):

    from os.path import isfile, isdir, join, abspath
    from glob import iglob

    return get_assembly_guids(file_path).decode('utf-8')
    
    
