import dataclasses
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Iterator, Optional

from depsurf.utils import manage_result_path

from .struct import StructInstance

if TYPE_CHECKING:
    from depsurf.linux_image import LinuxImage


@dataclass
class Tracepoint:
    class_name: str
    event_name: str
    func_name: str
    struct_name: str
    fmt_str: str
    func: dict
    struct: dict


class TracepointsExtractor:
    def __init__(self, img: "LinuxImage"):
        self.struct_types = img.struct_types
        self.func_types = img.func_types
        self.int_types = img.int_types

        self.filebytes = img.filebytes
        self.symtab = img.symtab

        self.event_names = {}
        self.class_names = {}
        for sym in self.symtab:
            t = sym["type"]
            name: str = sym["name"]
            if t == "STT_NOTYPE":
                # Ref: https://github.com/torvalds/linux/blob/49668688dd5a5f46c72f965835388ed16c596055/kernel/module.c#L2317
                if name == "__start_ftrace_events":
                    self.start_ftrace_events = sym["value"]
                elif name == "__stop_ftrace_events":
                    self.stop_ftrace_events = sym["value"]
            elif t == "STT_OBJECT":
                if name.startswith("event_class_"):
                    self.class_names[sym["value"]] = name.removeprefix("event_class_")
                elif name.startswith("event_"):
                    self.event_names[sym["value"]] = name.removeprefix("event_")

        for e in img.enum_types["(anon)"]["values"]:
            if e["name"] == "TRACE_EVENT_FL_TRACEPOINT":
                self.FLAG_TRACEPOINT = e["val"]
            elif e["name"] == "TRACE_EVENT_FL_IGNORE_ENABLE":
                self.FLAG_IGNORE_ENABLE = e["val"]

    def iter_event_ptrs(self) -> Iterator[int]:
        ptr_size = self.filebytes.ptr_size
        for ptr in range(self.start_ftrace_events, self.stop_ftrace_events, ptr_size):
            event_ptr = self.filebytes.get_int(ptr, ptr_size)
            if event_ptr == 0:
                logging.warning(f"Invalid event pointer: {ptr:x} -> {event_ptr:x}")
                continue
            yield event_ptr

    def get_tracepoint(self, ptr: int) -> Optional[Tracepoint]:
        # Ref: https://github.com/torvalds/linux/blob/2425bcb9240f8c97d793cb31c8e8d8d0a843fa29/include/linux/trace_events.h#L272
        event = StructInstance(
            struct_types=self.struct_types,
            int_types=self.int_types,
            filebytes=self.filebytes,
            name="trace_event_call",
            ptr=ptr,
        )
        class_name = self.class_names[event["class"]]
        flags = event["flags"]

        if flags & self.FLAG_IGNORE_ENABLE:
            # Ref: https://github.com/torvalds/linux/blob/6fbf71854e2ddea7c99397772fbbb3783bfe15b5/kernel/trace/trace_export.c#L172-L189
            logging.debug(f"Ignoring event {class_name}")
            return

        if not (flags & self.FLAG_TRACEPOINT):
            # Ref: https://github.com/torvalds/linux/blob/6fbf71854e2ddea7c99397772fbbb3783bfe15b5/include/linux/syscalls.h#L144
            return

        func_name = f"trace_event_raw_event_{class_name}"
        struct_name = f"trace_event_raw_{class_name}"

        func = self.func_types.get(func_name)
        struct = self.struct_types.get(struct_name)

        if func is None:
            logging.warning(f"Could not find function for {func_name}")
            return
        if struct is None:
            logging.warning(f"Could not find struct for {struct_name}")
            return

        return Tracepoint(
            class_name=class_name,
            event_name=self.event_names[ptr],
            func_name=func_name,
            struct_name=struct_name,
            func=func,
            struct=struct,
            fmt_str=self.filebytes.get_cstr(event["print_fmt"]),
        )

    def iter_tracepoints(self) -> Iterator[Tracepoint]:
        for ptr in self.iter_event_ptrs():
            info = self.get_tracepoint(ptr)
            if info:
                yield info


@manage_result_path
def dump_tracepoints(img: "LinuxImage", result_path):
    extractor = TracepointsExtractor(img)
    with open(result_path, "w") as f:
        for info in extractor.iter_tracepoints():
            json.dump(dataclasses.asdict(info), f)
            f.write("\n")


@dataclass
class Tracepoints:
    data: dict[str, Dict]

    @classmethod
    def from_dump(cls, path: Path):
        data = {}
        with open(path) as f:
            for line in f:
                info = json.loads(line)
                data[info["event_name"]] = info

        return cls(data=data)

    def __repr__(self):
        return f"Tracepoints ({len(self.data)}): {list(self.data.keys())}"
