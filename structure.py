import dataclasses
import json
from dataclasses import dataclass


@dataclass
class BpHeader:
    type_flag: int
    type_path: str
    root: str
    instance_name: str


@dataclass
class BpActorHeader(BpHeader):
    need_transform: bool

    rot_x: float
    rot_y: float
    rot_z: float
    rot_w: float

    pos_x: float
    pos_y: float
    pos_z: float

    scale_x: float
    scale_y: float
    scale_z: float

    placed_in_level: str


@dataclass
class BpComponentHeader(BpHeader):
    parent_actor_name: str


@dataclass
class BpObjectReference:
    level_name: str
    path_name: str


@dataclass
class TypedData:
    data_type: str
    data: dict


@dataclass
class BpProperty:
    name: str
    prop_type: str


@dataclass
class BpBoolProperty(BpProperty):
    value: bool


@dataclass
class BpByteProperty(BpProperty):
    type: str
    value: str or int


@dataclass
class BpEnumProperty(BpProperty):
    enum_type: str
    value: str


@dataclass
class BpFloatProperty(BpProperty):
    value: float


@dataclass
class BpIntProperty(BpProperty):
    value: int


@dataclass
class BpInt64Property(BpProperty):
    value: int


@dataclass
class BpObjectProperty(BpProperty):
    level_name: str
    path_name: str


@dataclass
class BpStructProperty(BpProperty):
    struct_type: str
    is_typed_data: bool
    data: list[BpProperty or None] or TypedData


@dataclass
class BpArrayElement:
    name: str
    prop_type: str


@dataclass
class BpArrayProperty(BpProperty):
    array_type: str


@dataclass
class BpStructArrayProperty(BpArrayProperty):
    guid: str
    data: list[BpStructProperty]


@dataclass
class BpValueArrayProperty(BpArrayProperty):
    data: list[any]


@dataclass
class BpObject:
    header: BpHeader
    parent_root: str
    parent_object_name: str
    references: list[BpObjectReference]
    properties: list[BpProperty or None]

    def dump_to_json(self):
        class EnhancedJSONEncoder(json.JSONEncoder):
            def default(self, o):
                if dataclasses.is_dataclass(o):
                    return dataclasses.asdict(o)
                return super().default(o)

        return json.dumps(self, cls=EnhancedJSONEncoder, indent=4)

