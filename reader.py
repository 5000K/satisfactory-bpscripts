from BufferReader import BufferReader
from BufferWriter import BufferWriter
from structure import BpHeader, BpObject, BpProperty, BpObjectProperty, BpStructProperty, TypedData, BpByteProperty


class BpReader:
    def __init__(self):
        pass

    def read(self, reader: BufferReader) -> object:
        pass

    def write(self, obj: object, writer: BufferWriter):
        pass


class BpHeaderReader(BpReader):
    def read(self, reader: BufferReader) -> BpHeader:
        uk1 = reader.next_int32()

        type_path = reader.next_string()
        root = reader.next_string()
        instance_name = reader.next_string()
        need_transform = reader.next_int32() == 1

        rot_x = reader.next_float()
        rot_y = reader.next_float()
        rot_z = reader.next_float()
        rot_w = reader.next_float()

        pos_x = reader.next_float()
        pos_y = reader.next_float()
        pos_z = reader.next_float()

        scale_x = reader.next_float()
        scale_y = reader.next_float()
        scale_z = reader.next_float()

        placed_in_level = reader.next_int32() == 1

        return BpHeader(type_path, root, instance_name, need_transform, rot_x, rot_y, rot_z, rot_w, pos_x, pos_y, pos_z, scale_x, scale_y, scale_z, placed_in_level)

    def write(self, obj: BpHeader, writer: BufferWriter):
        writer.next_string(obj.type_path)
        writer.next_string(obj.root)
        writer.next_string(obj.instance_name)
        writer.next_int32(1 if obj.need_transform else 0)

        writer.next_float(obj.rot_x)
        writer.next_float(obj.rot_y)
        writer.next_float(obj.rot_z)
        writer.next_float(obj.rot_w)

        writer.next_float(obj.pos_x)
        writer.next_float(obj.pos_y)
        writer.next_float(obj.pos_z)

        writer.next_float(obj.scale_x)
        writer.next_float(obj.scale_y)
        writer.next_float(obj.scale_z)


class BpPropertyReader(BpReader):
    def _read_byte_property(self, reader: BufferReader) -> BpByteProperty:
        name = reader.next_string()
        prop_type = reader.next_string()

        size = reader.next_int32()
        reader.skip_forward(4)  # skip 4 null bytes

        byte_type = reader.next_string()

        reader.skip_forward(1)

        if byte_type == "None":
            value = reader.next_byte()
        else:
            value = reader.next_string()

        return BpByteProperty(name, prop_type, byte_type, value)

    def _write_byte_property(self, obj: BpByteProperty, writer: BufferWriter):
        writer.next_string(obj.name)
        writer.next_string(obj.prop_type)
        write_size = writer.reserve_write_length()

        writer.next_bytes(b"\x00" * 4)

        writer.next_string(obj.type)
        writer.next_bytes(b"\x00")

        if obj.type == "None":
            writer.next_byte(obj.value)
        else:
            writer.next_string(obj.value)

        write_size()

    def _read_object_property(self, reader: BufferReader) -> BpObjectProperty:
        name = reader.next_string()
        prop_type = reader.next_string()

        size = reader.next_int32()
        reader.skip_forward(5)  # skip 5 null bytes

        level_name = reader.next_string()
        path_name = reader.next_string()

        return BpObjectProperty(name, prop_type, level_name, path_name)

    def _write_object_property(self, obj: BpObjectProperty, writer: BufferWriter):
        writer.next_string(obj.name)
        writer.next_string(obj.prop_type)
        write_size = writer.reserve_write_length()

        writer.next_bytes(b"\x00" * 5)

        writer.next_string(obj.level_name)
        writer.next_string(obj.path_name)

        write_size()

    def _read_struct_property(self, reader: BufferReader) -> BpStructProperty:
        name = reader.next_string()
        prop_type = reader.next_string()

        size = reader.next_int32()
        reader.skip_forward(4)  # skip 4 null bytes

        struct_type = reader.next_string()
        data = {}
        is_typed_data = True
        
        # skip padding
        reader.skip_forward(8 + 8 + 1)  # offset is 2 longs, 1 byte

        if struct_type == "Color":
            data["r"] = reader.next_byte()
            data["g"] = reader.next_byte()
            data["b"] = reader.next_byte()
            data["a"] = reader.next_byte()

        elif struct_type == "LinearColor":
            data["r"] = reader.next_float()
            data["g"] = reader.next_float()
            data["b"] = reader.next_float()
            data["a"] = reader.next_float()

        elif struct_type == "Vector" or struct_type == "Rotator":
            data["x"] = reader.next_float()
            data["y"] = reader.next_float()
            data["z"] = reader.next_float()

        elif struct_type == "Vector2D":
            data["x"] = reader.next_float()
            data["y"] = reader.next_float()

        elif struct_type == "Vector4" or struct_type == "Quat":
            data["x"] = reader.next_float()
            data["y"] = reader.next_float()
            data["z"] = reader.next_float()
            data["w"] = reader.next_float()

        else:
            data["values"] = []
            is_typed_data = False

            while True:
                sub_prop = BpPropertyReader().read(reader)
                data["values"].append(sub_prop)

                if sub_prop is None:
                    break

        if is_typed_data:
            data = TypedData(struct_type, data)
        else:
            data = data["values"]

        return BpStructProperty(name, prop_type, struct_type, is_typed_data, data)

    def _write_struct_property(self, obj: BpStructProperty, writer: BufferWriter):
        writer.next_string(obj.name)
        writer.next_string(obj.prop_type)
        write_size = writer.reserve_write_length()

        writer.next_bytes(b"\x00" * 4)

        writer.next_string(obj.struct_type)

        if obj.is_typed_data:
            if obj.struct_type == "Color":
                writer.next_byte(obj.data["r"])
                writer.next_byte(obj.data["g"])
                writer.next_byte(obj.data["b"])
                writer.next_byte(obj.data["a"])

            elif obj.struct_type == "LinearColor":
                writer.next_float(obj.data["r"])
                writer.next_float(obj.data["g"])
                writer.next_float(obj.data["b"])
                writer.next_float(obj.data["a"])

            elif obj.struct_type == "Vector" or obj.struct_type == "Rotator":
                writer.next_float(obj.data["x"])
                writer.next_float(obj.data["y"])
                writer.next_float(obj.data["z"])

            elif obj.struct_type == "Vector2D":
                writer.next_float(obj.data["x"])
                writer.next_float(obj.data["y"])

            elif obj.struct_type == "Vector4" or obj.struct_type == "Quat":
                writer.next_float(obj.data["x"])
                writer.next_float(obj.data["y"])
                writer.next_float(obj.data["z"])
                writer.next_float(obj.data["w"])

        else:
            for sub_prop in obj.data:
                BpPropertyReader().write(sub_prop, writer)

        write_size()

    def read(self, reader: BufferReader) -> BpProperty or None:
        jump_back = reader.set_jump_point()

        name = reader.next_string()

        if name == "None":
            return None

        prop_type = reader.next_string()

        jump_back()  # property readers will read the name and type again for completeness

        if prop_type == "StructProperty":
            return self._read_struct_property(reader)

        if prop_type == "ObjectProperty":
            return self._read_object_property(reader)

        if prop_type == "ByteProperty":
            return self._read_byte_property(reader)

        raise Exception(f"Unknown property type: {prop_type}")

    def write(self, obj: BpProperty or None, writer: BufferWriter):
        if obj is None:
            writer.next_string("None")
            return

        if isinstance(obj, BpObjectProperty):
            self._write_object_property(obj, writer)


class BpPropertiesReader(BpReader):
    def read(self, reader: BufferReader) -> list[BpProperty or None]:
        properties = []

        while True:
            prop = BpPropertyReader().read(reader)
            if prop is None:
                properties.append(None)
                break
            else:
                properties.append(prop)

        return properties

    def write(self, obj: list[BpProperty], writer: BufferWriter):
        pass


class BpBodyReader(BpReader):
    def read(self, reader: BufferReader) -> list[BpObject]:
        objects = []

        object_count = reader.next_int32()

        for i in range(object_count):
            header = BpHeaderReader().read(reader)
            obj = BpObject(header, "", "", [])
            objects.append(obj)

        uk1 = reader.next_int32()
        uk2 = reader.next_int32()

        for i in range(object_count):
            print(f"Reading object {i}")
            reader.print_offset_hex()

            obj = objects[i]

            size = reader.next_int32()

            obj.parent_root = reader.next_string()
            obj.parent_object_name = reader.next_string()

            reader.skip_forward(4)  # skip 4 null bytes
            reader.print_offset_hex()

            obj.properties = BpPropertiesReader().read(reader)
            reader.skip_forward(4)

            objects[i] = obj

        return objects

    def write(self, obj: list[BpObject], writer: BufferWriter):
        pass
