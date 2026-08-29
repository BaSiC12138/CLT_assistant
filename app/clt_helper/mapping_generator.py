from __future__ import annotations

import argparse
import json
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

OUTER_HEADER_SIZE = 32
OUTER_CRC_SIZE = 4
OUTER_VERSION = 4
INNER_FORMAT_VERSION = 10
INNER_BLOCK_MARKER = 0x80
INNER_FIXED_HEADER_SIZE = 81
DEVICE_PREFIX_SIZE = 32
PORT_RECORD_SIZE = 28
CARD_RECORD_SIZE = 15
CARD_COUNT_OFFSET = 69
COLUMN_COUNT_OFFSET = 71
ROW_COUNT_OFFSET = 73
DEVICE_COUNT_OFFSET = 79
CRC_POLYNOMIAL = 0xEDB88320
MAX_U8 = 0xFF
MAX_U16 = 0xFFFF
MAX_U32 = 0xFFFFFFFF
MAX_OUTPUT_PORT_SLOTS = 800
@dataclass(frozen=True, kw_only=True)
class Area:
    x: int
    y: int
    width: int
    height: int
@dataclass(frozen=True, kw_only=True)
class Card:
    device: int
    port: int
    chain: int
    area: Area
@dataclass(frozen=True, kw_only=True)
class MappingConfig:
    output_port_slots: int
    columns: int
    rows: int
    unused_port_size: Area
    cards: tuple[Card, ...]
    port_areas: tuple[tuple[int, Area], ...]
@dataclass(frozen=True, kw_only=True)
class TemplateData:
    outer_header: bytes
    inner_header: bytes
    device_prefix: bytes
    port_records: tuple[bytes, ...]
    port_suffix: bytes
def require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value
def require_int(value: Any, label: str, bounds: tuple[int, int]) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    minimum, maximum = bounds
    if not minimum <= value <= maximum:
        raise ValueError(f"{label} must be in range {minimum}..{maximum}")
    return value
def read_int(data: Mapping[str, Any], key: str, bounds: tuple[int, int]) -> int:
    if key not in data:
        raise ValueError(f"missing required field: {key}")
    return require_int(data[key], key, bounds)
def parse_area(value: Any, label: str, bounds: tuple[int, int] = (MAX_U16, MAX_U16)) -> Area:
    data = require_mapping(value, label)
    coordinate_max, size_max = bounds
    return Area(
        x=read_int(data, "x", (0, coordinate_max)),
        y=read_int(data, "y", (0, coordinate_max)),
        width=read_int(data, "width", (1, size_max)),
        height=read_int(data, "height", (1, size_max)),
    )
def parse_card(value: Any, index: int) -> Card:
    data = require_mapping(value, f"cards[{index}]")
    area = parse_area(data, f"cards[{index}]")
    return Card(
        device=read_int(data, "device", (1, MAX_U8)),
        port=read_int(data, "port", (1, MAX_OUTPUT_PORT_SLOTS)),
        chain=read_int(data, "chain", (1, MAX_U16)),
        area=area,
    )
def parse_port_areas(value: Any) -> tuple[tuple[int, Area], ...]:
    data = require_mapping(value, "port_areas")
    parsed = []
    for key, area_value in data.items():
        port = require_int(int(key), f"port_areas.{key}", (1, MAX_OUTPUT_PORT_SLOTS))
        parsed.append((port, parse_area(area_value, f"port_areas.{key}", (MAX_U32, MAX_U32))))
    return tuple(sorted(parsed))
def parse_config(value: Any) -> MappingConfig:
    data = require_mapping(value, "config")
    screen = require_mapping(data.get("screen"), "screen")
    cards_value = data.get("cards")
    if not isinstance(cards_value, Sequence) or isinstance(cards_value, (str, bytes)):
        raise ValueError("cards must be an array")
    cards = tuple(parse_card(item, index) for index, item in enumerate(cards_value))
    default_size = parse_area(data.get("unused_port_size"), "unused_port_size", (MAX_U32, MAX_U32))
    config = MappingConfig(
        output_port_slots=read_int(data, "output_port_slots", (1, MAX_OUTPUT_PORT_SLOTS)),
        columns=read_int(screen, "columns", (1, MAX_U16)),
        rows=read_int(screen, "rows", (1, MAX_U16)),
        unused_port_size=default_size,
        cards=tuple(sorted(cards, key=lambda card: (card.device, card.port, card.chain))),
        port_areas=parse_port_areas(data.get("port_areas", {})),
    )
    validate_config(config)
    return config
def validate_config(config: MappingConfig) -> None:
    if not config.cards:
        raise ValueError("cards must contain at least one receiver card")
    if len(config.cards) > config.columns * config.rows:
        raise ValueError("card count exceeds screen.columns * screen.rows")
    if any(card.device != 1 for card in config.cards):
        raise ValueError("this V10 generator currently supports device=1 only")
    if any(card.port > config.output_port_slots for card in config.cards):
        raise ValueError("a card uses a port beyond output_port_slots")
    validate_card_identity(config.cards)
    overrides = dict(config.port_areas)
    if any(port > config.output_port_slots for port in overrides):
        raise ValueError("port_areas contains a port beyond output_port_slots")
def validate_card_identity(cards: tuple[Card, ...]) -> None:
    identities = [(card.device, card.port, card.chain) for card in cards]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate device/port/chain identity")
    ports = sorted({card.port for card in cards})
    for port in ports:
        chains = [card.chain for card in cards if card.port == port]
        if chains != list(range(1, len(chains) + 1)):
            raise ValueError(f"port {port} chain values must be consecutive from 1")
def calculate_crc(content: bytes) -> int:
    table = build_crc_table()
    checksum = 0
    for byte in content:
        checksum = (checksum >> 8) ^ table[(checksum ^ byte) & MAX_U8]
    return checksum & MAX_U32
def build_crc_table() -> tuple[int, ...]:
    table = []
    for index in range(256):
        value = index
        for _ in range(8):
            value = (value >> 1) ^ CRC_POLYNOMIAL if value & 1 else value >> 1
        table.append(value)
    return tuple(table)
def decode_outer(data: bytes) -> tuple[bytes, bytes]:
    if len(data) < OUTER_HEADER_SIZE + OUTER_CRC_SIZE:
        raise ValueError("template file is incomplete")
    stored_crc = struct.unpack_from("<I", data, len(data) - OUTER_CRC_SIZE)[0]
    if stored_crc != calculate_crc(data[:-OUTER_CRC_SIZE]):
        raise ValueError("template CRC check failed")
    version, compressed_size, payload_size, flags = struct.unpack_from("<4I", data, 16)
    if version != OUTER_VERSION or flags != 0:
        raise ValueError("unsupported outer mapping version or flags")
    compressed = data[OUTER_HEADER_SIZE : OUTER_HEADER_SIZE + compressed_size]
    if len(data) != OUTER_HEADER_SIZE + compressed_size + OUTER_CRC_SIZE:
        raise ValueError("outer mapping file length mismatch")
    payload = zlib.decompress(compressed)
    if len(payload) != payload_size:
        raise ValueError("template payload length mismatch")
    return data[:OUTER_HEADER_SIZE], payload
def parse_template(data: bytes) -> TemplateData:
    outer_header, payload = decode_outer(data)
    if len(payload) < INNER_FIXED_HEADER_SIZE + DEVICE_PREFIX_SIZE:
        raise ValueError("template inner payload is incomplete")
    if struct.unpack_from("<H", payload, 0)[0] != len(payload):
        raise ValueError("template inner payload length mismatch")
    if payload[2] != INNER_FORMAT_VERSION or payload[3] != INNER_BLOCK_MARKER:
        raise ValueError("only inner mapping format V10 is supported")
    device_count = struct.unpack_from("<H", payload, DEVICE_COUNT_OFFSET)[0]
    if device_count != 1:
        raise ValueError("template must contain exactly one sender device")
    port_slots = struct.unpack_from("<H", payload, INNER_FIXED_HEADER_SIZE)[0]
    device_end = INNER_FIXED_HEADER_SIZE + DEVICE_PREFIX_SIZE
    table_end = device_end + port_slots * PORT_RECORD_SIZE
    card_count = struct.unpack_from("<H", payload, CARD_COUNT_OFFSET)[0]
    expected_end = table_end + card_count * CARD_RECORD_SIZE
    if expected_end != len(payload):
        raise ValueError("template contains unsupported trailing or variable records")
    records = tuple(
        payload[device_end + index * PORT_RECORD_SIZE : device_end + (index + 1) * PORT_RECORD_SIZE]
        for index in range(port_slots)
    )
    if not records:
        raise ValueError("template has no output port records")
    return TemplateData(
        outer_header=outer_header,
        inner_header=payload[:INNER_FIXED_HEADER_SIZE],
        device_prefix=payload[INNER_FIXED_HEADER_SIZE:device_end],
        port_records=records,
        port_suffix=records[0][16:],
    )
def union_area(cards: tuple[Card, ...], port: int) -> Area | None:
    selected = [card.area for card in cards if card.port == port]
    if not selected:
        return None
    left = min(area.x for area in selected)
    top = min(area.y for area in selected)
    right = max(area.x + area.width for area in selected)
    bottom = max(area.y + area.height for area in selected)
    return Area(x=left, y=top, width=right - left, height=bottom - top)
def build_port_records(template: TemplateData, config: MappingConfig) -> bytes:
    overrides = dict(config.port_areas)
    output = bytearray()
    for port in range(1, config.output_port_slots + 1):
        area = overrides.get(port) or union_area(config.cards, port) or config.unused_port_size
        suffix = template.port_records[port - 1][16:] if port <= len(template.port_records) else template.port_suffix
        output.extend(struct.pack("<IIII", area.x, area.y, area.width, area.height))
        output.extend(suffix)
    return bytes(output)
def build_card_record(card: Card) -> bytes:
    record = bytearray(CARD_RECORD_SIZE)
    zero_based_port = card.port - 1
    struct.pack_into("<H", record, 0, card.chain - 1)
    record[2] = card.device
    record[4] = zero_based_port // 256
    record[5] = zero_based_port % 256
    struct.pack_into("<HHHH", record, 7, card.area.x, card.area.y, card.area.width, card.area.height)
    return bytes(record)
def build_payload(template: TemplateData, config: MappingConfig) -> bytes:
    header = bytearray(template.inner_header)
    struct.pack_into("<H", header, CARD_COUNT_OFFSET, len(config.cards))
    struct.pack_into("<H", header, COLUMN_COUNT_OFFSET, config.columns)
    struct.pack_into("<H", header, ROW_COUNT_OFFSET, config.rows)
    device_prefix = bytearray(template.device_prefix)
    struct.pack_into("<H", device_prefix, 0, config.output_port_slots)
    cards = b"".join(build_card_record(card) for card in config.cards)
    payload = header + device_prefix + build_port_records(template, config) + cards
    if len(payload) > MAX_U16:
        raise ValueError("generated inner payload exceeds uint16 length")
    struct.pack_into("<H", payload, 0, len(payload))
    return bytes(payload)
def wrap_payload(template: TemplateData, payload: bytes) -> bytes:
    compressed = zlib.compress(payload, level=6)
    header = bytearray(template.outer_header)
    struct.pack_into("<I", header, 20, len(compressed))
    struct.pack_into("<I", header, 24, len(payload))
    content = bytes(header) + compressed
    return content + struct.pack("<I", calculate_crc(content))
def generate_mapping(template_path: Path, output_path: Path, config_data: Any) -> None:
    config = parse_config(config_data)
    template = parse_template(template_path.read_bytes())
    generated = wrap_payload(template, build_payload(template, config))
    verify_generated(generated, config)
    output_path.write_bytes(generated)
def verify_generated(data: bytes, config: MappingConfig) -> None:
    _, payload = decode_outer(data)
    card_count = struct.unpack_from("<H", payload, CARD_COUNT_OFFSET)[0]
    columns = struct.unpack_from("<H", payload, COLUMN_COUNT_OFFSET)[0]
    rows = struct.unpack_from("<H", payload, ROW_COUNT_OFFSET)[0]
    slots = struct.unpack_from("<H", payload, INNER_FIXED_HEADER_SIZE)[0]
    if (card_count, columns, rows, slots) != (
        len(config.cards), config.columns, config.rows, config.output_port_slots
    ):
        raise ValueError("generated mapping failed structural verification")
    card_offset = INNER_FIXED_HEADER_SIZE + DEVICE_PREFIX_SIZE + slots * PORT_RECORD_SIZE
    if len(payload) != card_offset + card_count * CARD_RECORD_SIZE:
        raise ValueError("generated mapping record length mismatch")
    for index, expected in enumerate(config.cards):
        offset = card_offset + index * CARD_RECORD_SIZE
        actual = payload[offset : offset + CARD_RECORD_SIZE]
        if actual != build_card_record(expected):
            raise ValueError(f"generated receiver card {index + 1} verification failed")
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate ColorLight LEDSetting V10 .mapping files")
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()
def main() -> None:
    arguments = parse_arguments()
    config_data = json.loads(arguments.config.read_text(encoding="utf-8"))
    generate_mapping(arguments.template, arguments.output, config_data)
    print(arguments.output.resolve())

if __name__ == "__main__":
    main()
