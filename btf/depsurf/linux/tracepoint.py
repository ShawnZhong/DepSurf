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

        ptr_size = img.ptr_size
        for ptr in range(self.start_ftrace_events, self.stop_ftrace_events, ptr_size):
            event_ptr = img.get_int(ptr, ptr_size)
            if event_ptr == 0:
                logging.warning(f"Invalid event pointer: {ptr:x} -> {event_ptr:x}")
                continue
            res = self.get_tracepoint(event_ptr)
            if res is not None:
                name, func, struct = res
                self.funcs[name] = func
                self.events[name] = struct

    @property
    def start_ftrace_events(self):
        return self.img.symtab.get_value_by_name("__start_ftrace_events")

    @property
    def stop_ftrace_events(self):
        return self.img.symtab.get_value_by_name("__stop_ftrace_events")

    @cached_property
    def TRACE_EVENT_FL_TRACEPOINT(self):
        return self.img.btf.enum_values["TRACE_EVENT_FL_TRACEPOINT"]

    @cached_property
    def event_val_to_name(self):
        objects = self.img.symtab.objects
        return {
            row["value"]: row["name"].removeprefix("event_")
            for _, row in objects[objects.name.str.startswith("event_")].iterrows()
        }

    @cached_property
    def event_class_val_to_name(self):
        objects = self.img.symtab.objects
        return {
            row["value"]: row["name"].removeprefix("event_class_")
            for _, row in objects[
                objects.name.str.startswith("event_class_")
            ].iterrows()
        }

    def get_tp_func(self, name: str):
        btf = self.img.btf
        for func_prefix in ["trace_event_raw_event_", "perf_trace_", "__traceiter_"]:
            func = btf.get_func(f"{func_prefix}{name}")
            if func:
                return func

        logging.warning(f"Could not find function for {name}")

        # typedef = btf.get(Kind.TYPEDEF, f"btf_trace_{name}")
        # if typedef is not None:
        #     func = typedef["type"].copy()
        #     assert func["kind"] == Kind.PTR
        #     assert func["type"]["kind"] == Kind.FUNC_PROTO
        #     func["kind"] = Kind.FUNC.name
        #     return func

    def get_tracepoint(self, ptr: int):
        event = self.img.get_struct_instance("trace_event_call", ptr)

        # Skip non-tracepoint events
        if not (event["flags"] & self.TRACE_EVENT_FL_TRACEPOINT):
            return

        event_name = self.event_val_to_name[ptr]
        event_class_name = self.event_class_val_to_name[event["class"]]

        func_name = f"trace_event_raw_event_{event_class_name}"
        struct_name = f"trace_event_raw_{event_class_name}"

        func = self.img.btf.get_func(func_name)
        struct = self.img.btf.get_struct(struct_name)

        if func is None:
            logging.warning(f"Could not find function {func_name}")
            return None
        if struct is None:
            logging.warning(f"Could not find struct {struct_name}")
            return None

        return (event_name, func, struct)

        # fmt_ptr = event["print_fmt"]
        # fmt = self.img.get_cstr(fmt_ptr)
        # print(fmt_ptr)

        # tp = self.img.get_struct_instance("tracepoint", event["tp"])
        # name = self.img.get_cstr(tp["name"])

        # event_class = self.img.get_struct_instance("trace_event_class", event_class_ptr)

    def __repr__(self):
        return f"Tracepoints ({len(self.funcs)}): {list(self.funcs.keys())}"
