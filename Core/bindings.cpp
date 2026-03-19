#include <pybind11/pybind11.h>
#include "matching_engine.h"
#include "signal_engine.h"

namespace py = pybind11;

PYBIND11_MODULE(core, m) {
    py::class_<MatchingEngine>(m, "MatchingEngine")
        .def(py::init<>())
        .def("process_order", &MatchingEngine::process_order);

    m.def("microprice", [](MatchingEngine& engine) {
        return SignalEngine::microprice(engine.ob);
    });
}
