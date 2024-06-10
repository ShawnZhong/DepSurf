import dataclasses
import json
import logging
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Iterator, Optional

from depsurf.btf import BTF
from depsurf.utils import check_result_path

from .filebytes import FileBytes
from .struct import StructInstance
from .symtab import SymbolTable


@dataclass
class TracepointInfo:
    flags: int
    class_name: str
    event_name: str
    func_name: str
    struct_name: str
    fmt_str: str
    func: dict
    struct: dict


class TracepointsExtractor:
    def __init__(self, btf: BTF, filebytes: FileBytes, symtab: SymbolTable):
        self.btf = btf
        self.filebytes = filebytes
        self.symtab = symtab

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

    def iter_event_ptrs(self) -> Iterator[int]:
        ptr_size = self.filebytes.ptr_size
        for ptr in range(self.start_ftrace_events, self.stop_ftrace_events, ptr_size):
            event_ptr = self.filebytes.get_int(ptr, ptr_size)
            if event_ptr == 0:
                logging.warning(f"Invalid event pointer: {ptr:x} -> {event_ptr:x}")
                continue
            yield event_ptr

    def get_tracepoint(self, ptr: int) -> Optional[TracepointInfo]:
        # Ref: https://github.com/torvalds/linux/blob/2425bcb9240f8c97d793cb31c8e8d8d0a843fa29/include/linux/trace_events.h#L272
        event = StructInstance(self.btf, self.filebytes, "trace_event_call", ptr)
        class_name = self.class_names[event["class"]]
        flags = event["flags"]

        if flags & self.FLAG_IGNORE_ENABLE:
            # Ref: https://github.com/torvalds/linux/blob/6fbf71854e2ddea7c99397772fbbb3783bfe15b5/kernel/trace/trace_export.c#L172-L189
            logging.debug(f"Ignoring event {class_name}")
            return

        if not (flags & self.FLAG_TRACEPOINT):
            # Ref: https://github.com/torvalds/linux/blob/6fbf71854e2ddea7c99397772fbbb3783bfe15b5/include/linux/syscalls.h#L144
            event_name = self.filebytes.get_cstr(event["name"])
            return
            # TracepointInfo(
            #     flags=flags,
            #     class_name=class_name,
            #     event_name=event_name,
            #     func_name=None,
            #     struct_name=None,
            #     func=None,
            #     struct=None,
            #     fmt_str=None,
            # )

        func_name = f"trace_event_raw_event_{class_name}"
        struct_name = f"trace_event_raw_{class_name}"

        func = self.btf.get_func(func_name)
        struct = self.btf.get_struct(struct_name)

        if func is None:
            logging.warning(f"Could not find function for {func_name}")
            return
        if struct is None:
            logging.warning(f"Could not find struct for {struct_name}")
            return

        return TracepointInfo(
            flags=flags,
            class_name=class_name,
            event_name=self.event_names[ptr],
            func_name=func_name,
            struct_name=struct_name,
            func=func,
            struct=struct,
            fmt_str=self.filebytes.get_cstr(event["print_fmt"]),
        )

    def iter_tracepoints(self) -> Iterator[TracepointInfo]:
        for ptr in self.iter_event_ptrs():
            info = self.get_tracepoint(ptr)
            if info:
                yield info

    @cached_property
    def FLAG_TRACEPOINT(self):
        return self.btf.enum_values["TRACE_EVENT_FL_TRACEPOINT"]

    @cached_property
    def FLAG_IGNORE_ENABLE(self):
        return self.btf.enum_values["TRACE_EVENT_FL_IGNORE_ENABLE"]

    # tp = self.img.get_struct_instance("tracepoint", event["tp"])
    # name = self.filebytes.get_cstr(tp["name"])

    # event_class = self.img.get_struct_instance("trace_event_class", event_class_ptr)

    # def get_tp_func(self, name: str):
    #     btf = self.btf
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
    extractor = TracepointsExtractor(img.btf, img.filebytes, img.symtab)
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
        return {name: info.func for name, info in self.data.items() if info.func}

    @property
    def structs(self):
        return {name: info.struct for name, info in self.data.items() if info.struct}

    def __repr__(self):
        return f"Tracepoints ({len(self.funcs)}): {list(self.funcs.keys())}"
