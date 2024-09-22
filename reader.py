from BufferReader import BufferReader
from BufferWriter import BufferWriter
from structure import BpHeader, BpObject, BpProperty, BpObjectProperty, BpStructProperty, TypedData


class BpReader:
    def __init__(self):
        pass

    def read(self, reader: BufferReader) -> object:
        pass

    def write(self, obj: object, writer: BufferWriter):
        pass


class BpHeaderReader(BpReader):
    def read(self, reader: BufferReader) -> BpHeader:
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

        return BpHeader(type_path, root, instance_name, need_transform, rot_x, rot_y, rot_z, rot_w, pos_x, pos_y, pos_z, scale_x, scale_y, scale_z)

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

    def write(self, obj: BpProperty or None, writer: BufferWriter):
        if obj is None:
            writer.next_string("None")
            return

        writer.next_string(obj.name)
        writer.next_string(obj.prop_type)

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


class BpObjectReader(BpReader):
    def read(self, reader: BufferReader) -> BpObject:
        header = BpHeaderReader().read(reader)
        parent_root = reader.next_string()
        parent_object_name = reader.next_string()

        reader.skip_forward(4)

        properties = BpPropertiesReader().read(reader)

        return BpObject(header, parent_root, parent_object_name, properties)

    def write(self, obj: BpObject, writer: BufferWriter):
        pass

