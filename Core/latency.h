#pragma once
#include <chrono>

class Timer {
public:
    std::chrono::high_resolution_clock::time_point start;

    void tic() {
        start = std::chrono::high_resolution_clock::now();
    }

    long long toc() {
        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    }
};
