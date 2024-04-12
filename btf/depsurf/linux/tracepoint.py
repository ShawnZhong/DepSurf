import logging
from functools import cached_property

from .image import LinuxImage, Struct
from depsurf.btf import Kind


class Tracepoints:
    def __init__(self, img: LinuxImage):
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

    def is_tracepoint(self, trace_event_call: Struct):
        assert trace_event_call.name == "trace_event_call"
        flags = trace_event_call.get("flags")
        return flags & self.TRACE_EVENT_FL_TRACEPOINT

    def get_tp_name(self, tp_ptr: int):
        tp = Struct(self.img, "tracepoint", tp_ptr)
        name = tp.get("name")
        return self.img.get_cstr(name)

    def get_event(self, trace_event_class_ptr: int):
        trace_event_class = Struct(self.img, "trace_event_class", trace_event_class_ptr)

        probe = trace_event_class.get("probe")
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

    def get_tracepoint(self, trace_event_call_ptr: int):
        trace_event_call = Struct(self.img, "trace_event_call", trace_event_call_ptr)

        if not self.is_tracepoint(trace_event_call):
            return

        name = self.get_tp_name(trace_event_call.get("tp"))
        func, struct = self.get_event(trace_event_call.get("class"))
        if func is None:
            func = self.get_tp_func(name)
        if func is None:
            return None

        return (name, func, struct)

    def __repr__(self):
        return f"Tracepoints: {list(self.funcs.keys())}"
