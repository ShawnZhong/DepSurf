import logging
from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .image import LinuxImage


class Tracepoints:
    def __init__(self, img: "LinuxImage"):
        self.img = img
        self.funcs = {}
        self.events = {}

        start_ftrace_events = img.symtab.get_value_by_name("__start_ftrace_events")
        stop_ftrace_events = img.symtab.get_value_by_name("__stop_ftrace_events")
        for ptr in range(start_ftrace_events, stop_ftrace_events, 8):
            res = self.get_tracepoint(img.get_int(ptr, 8))
            if res is not None:
                name, func, struct = res
                self.funcs[name] = func
                self.events[name] = struct

    @cached_property
    def TRACE_EVENT_FL_TRACEPOINT(self):
        return self.img.btf.enum_values["TRACE_EVENT_FL_TRACEPOINT"]

    def get_tp_name(self, tp_ptr: int):
        tp = self.img.get_struct_instance("tracepoint", tp_ptr)
        return self.img.get_cstr(tp["name"])

    def get_event(self, ptr: int):
        event_class = self.img.get_struct_instance("trace_event_class", ptr)

        probe = event_class["probe"]
        probe_name = self.img.symtab.get_name_by_value(probe)
        func = self.img.btf.get_func(probe_name)

        assert probe_name.startswith("trace_event_raw_event_")
        event_name = probe_name.replace("trace_event_raw_event_", "trace_event_raw_")
        struct = self.img.btf.get_struct(event_name)
        assert struct is not None, f"Could not find event struct {event_name}"

        return func, struct

    def get_tp_func(self, name: str):
        btf = self.img.btf
        for func_prefix in ["perf_trace_", "__traceiter_"]:
            func = btf.get_func(f"{func_prefix}{name}")
            if func:
                return func

        # typedef = btf.get(Kind.TYPEDEF, f"btf_trace_{name}")
        # if typedef is not None:
        #     func = typedef["type"].copy()
        #     assert func["kind"] == Kind.PTR
        #     assert func["type"]["kind"] == Kind.FUNC_PROTO
        #     func["kind"] = Kind.FUNC.name
        #     return func

        logging.warning(f"Could not find function for {name}")

    def get_tracepoint(self, ptr: int):
        event = self.img.get_struct_instance("trace_event_call", ptr)

        # Skip non-tracepoint events
        if not (event["flags"] & self.TRACE_EVENT_FL_TRACEPOINT):
            return

        name = self.get_tp_name(event["tp"])
        func, struct = self.get_event(event["class"])
        if func is None:
            func = self.get_tp_func(name)
        if func is None:
            return None

        return (name, func, struct)

    def __repr__(self):
        return f"Tracepoints: {list(self.funcs.keys())}"
