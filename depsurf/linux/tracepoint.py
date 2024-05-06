import dataclasses
import logging
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Iterator
from pathlib import Path
import json

from depsurf.utils import check_result_path

if TYPE_CHECKING:
    from ..img import LinuxImage


@dataclass
class TracepointInfo:
    event_name: str
    func_name: str
    struct_name: str
    fmt_str: str
    func: dict
    struct: dict


class TracepointsExtractor:
    def __init__(self, img: "LinuxImage"):
        self.img = img
        self.event_names = {}
        self.event_class_names = {}
        for sym in self.img.symtab:
            # Ref: https://github.com/torvalds/linux/blob/49668688dd5a5f46c72f965835388ed16c596055/kernel/module.c#L2317
            t = sym["type"]
            name = sym["name"]
            if t == "STT_NOTYPE":
                if name == "__start_ftrace_events":
                    self.start_ftrace_events = sym["value"]
                elif name == "__stop_ftrace_events":
                    self.stop_ftrace_events = sym["value"]
            elif t == "STT_OBJECT":
                if name.startswith("event_class_"):
                    self.event_class_names[sym["value"]] = name.removeprefix(
                        "event_class_"
                    )
                elif name.startswith("event_"):
                    self.event_names[sym["value"]] = name.removeprefix("event_")

    def iter_event_ptrs(self) -> Iterator[int]:
        ptr_size = self.img.ptr_size
        for ptr in range(self.start_ftrace_events, self.stop_ftrace_events, ptr_size):
            event_ptr = self.img.get_int(ptr, ptr_size)
            if event_ptr == 0:
                logging.warning(f"Invalid event pointer: {ptr:x} -> {event_ptr:x}")
                continue
            yield event_ptr

    def iter_tracepoints(self) -> Iterator[TracepointInfo]:
        for ptr in self.iter_event_ptrs():
            # Ref: https://github.com/torvalds/linux/blob/2425bcb9240f8c97d793cb31c8e8d8d0a843fa29/include/linux/trace_events.h#L272
            event = self.img.get_struct_instance("trace_event_call", ptr)

            # Skip non-tracepoint events
            if not (event["flags"] & self.TRACEPOINT_FLAG):
                continue

            event_class_name = self.event_class_names[event["class"]]

            func_name = f"trace_event_raw_event_{event_class_name}"
            struct_name = f"trace_event_raw_{event_class_name}"

            func = self.img.btf.get_func(func_name)
            struct = self.img.btf.get_struct(struct_name)

            if func is None:
                logging.warning(f"Could not find function for {func_name}")
                continue
            if struct is None:
                logging.warning(f"Could not find struct for {struct_name}")
                continue

            yield TracepointInfo(
                event_name=self.event_names[ptr],
                func_name=func_name,
                struct_name=struct_name,
                func=func,
                struct=struct,
                fmt_str=self.img.get_cstr(event["print_fmt"]),
            )

    @cached_property
    def TRACEPOINT_FLAG(self):
        return self.img.btf.enum_values["TRACE_EVENT_FL_TRACEPOINT"]

    # tp = self.img.get_struct_instance("tracepoint", event["tp"])
    # name = self.img.get_cstr(tp["name"])

    # event_class = self.img.get_struct_instance("trace_event_class", event_class_ptr)

    # def get_tp_func(self, name: str):
    #     btf = self.img.btf
    #     for func_prefix in ["trace_event_raw_event_", "perf_trace_", "__traceiter_"]:
    #         func = btf.get_func(f"{func_prefix}{name}")
    #         if func:
    #             return func

    #     logging.warning(f"Could not find function for {name}")

    #     typedef = btf.get(Kind.TYPEDEF, f"btf_trace_{name}")
    #     if typedef is not None:
    #         func = typedef["type"].copy()
    #         assert func["kind"] == Kind.PTR
    #         assert func["type"]["kind"] == Kind.FUNC_PROTO
    #         func["kind"] = Kind.FUNC.name
    #         return func


@check_result_path
def dump_tracepoints(img, result_path):
    extractor = TracepointsExtractor(img)
    with open(result_path, "w") as f:
        for info in extractor.iter_tracepoints():
            json.dump(dataclasses.asdict(info), f)
            f.write("\n")
    logging.info(f"Saved tracepoints to {result_path}")


@dataclass
class Tracepoints:
    data: dict[str, TracepointInfo]

    @classmethod
    def from_dump(cls, path: Path):
        data = {}
        with open(path) as f:
            for line in f:
                info = json.loads(line)
                data[info["event_name"]] = TracepointInfo(**info)

        return cls(data=data)

    @property
    def funcs(self):
        return {name: info.func for name, info in self.data.items()}

    @property
    def structs(self):
        return {name: info.struct for name, info in self.data.items()}

    def __repr__(self):
        return f"Tracepoints ({len(self.funcs)}): {list(self.funcs.keys())}"
