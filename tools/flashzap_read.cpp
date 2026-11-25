// Read-only FlashZap RAM-downloader harness.
// Uses the vendor FlashZap worker DLLs but never calls flash/erase/write.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <cstdint>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

using Fn1 = int(__thiscall*)(void*);
using FnU16 = int(__thiscall*)(void*, uint16_t);
using FnU32 = int(__thiscall*)(void*, uint32_t);
using FnRead = int(__thiscall*)(void*, uint8_t*, uint32_t, uint32_t);
using CtorStr = void(__thiscall*)(void*, const char*);
using CtorVoid = void(__thiscall*)(void*);
using FnInit = int(__thiscall*)(void*, void*);

static void* Proc(HMODULE mod, const char* name) {
    auto p = GetProcAddress(mod, name);
    if (!p) std::printf("missing export: %s\n", name);
    return reinterpret_cast<void*>(p);
}

static bool WriteFileBytes(const std::string& path, const std::vector<uint8_t>& data) {
    FILE* f = std::fopen(path.c_str(), "wb");
    if (!f) return false;
    const size_t n = std::fwrite(data.data(), 1, data.size(), f);
    std::fclose(f);
    return n == data.size();
}

static void WriteSrec(const std::string& path, const std::vector<uint8_t>& data,
                      uint32_t base) {
    FILE* f = std::fopen(path.c_str(), "wb");
    if (!f) return;
    std::fprintf(f, "S00600004844521B\n");
    for (size_t off = 0; off < data.size(); off += 32) {
        const size_t n = (data.size() - off < 32) ? data.size() - off : 32;
        uint8_t rec[5 + 32];
        rec[0] = uint8_t((base + off) >> 24);
        rec[1] = uint8_t((base + off) >> 16);
        rec[2] = uint8_t((base + off) >> 8);
        rec[3] = uint8_t(base + off);
        std::memcpy(rec + 4, data.data() + off, n);
        unsigned sum = 0;
        for (size_t i = 0; i < n + 4; ++i) sum += rec[i];
        rec[n + 4] = uint8_t(~sum);
        std::fprintf(f, "S3%02X%08X", unsigned(n + 5), unsigned(base + off));
        for (size_t i = 0; i < n + 1; ++i) std::fprintf(f, "%02X", rec[4 + i]);
        std::fputc('\n', f);
    }
    std::fprintf(f, "S705%08X%02X\n", unsigned(base), 0);
    std::fclose(f);
}

int main(int argc, char** argv) {
    if (argc < 3) {
        std::printf("usage: flashzap_read <flashzap-dir> <COMx> [out.srec] [start] [length] [baud]\n");
        return 2;
    }
    const std::string dir = argv[1];
    const std::string portName = argv[2];
    const std::string out = argc >= 4 ? argv[3] : "flashzap-read.srec";
    const uint32_t start = argc >= 5 ? uint32_t(std::strtoul(argv[4], nullptr, 0)) : 0;
    const uint32_t length = argc >= 6 ? uint32_t(std::strtoul(argv[5], nullptr, 0)) : 0x400000;
    const uint32_t baud = argc >= 7 ? uint32_t(std::strtoul(argv[6], nullptr, 0)) : 115200;

    SetDllDirectoryA(dir.c_str());
    HMODULE com = LoadLibraryA((dir + "\\fzap_com.dll").c_str());
    HMODULE worker = LoadLibraryA((dir + "\\fzap_worker.dll").c_str());
    if (!com || !worker) {
        std::printf("cannot load FlashZap DLLs (com=%p worker=%p)\n", com, worker);
        return 2;
    }

    auto rsCtor = reinterpret_cast<CtorStr>(Proc(com, "??0RS232Port@@QAE@PBD@Z"));
    auto rsOpen = reinterpret_cast<Fn1>(Proc(com, "?openPort@RS232Port@@UAEHXZ"));
    auto rsBaud = reinterpret_cast<FnU32>(Proc(com, "?changeBaudRate@RS232Port@@UAEHI@Z"));
    auto fzCtor = reinterpret_cast<CtorVoid>(Proc(worker, "??0FZAPworker@@QAE@XZ"));
    auto fzInit = reinterpret_cast<FnInit>(Proc(worker, "?FZAPinit@FZAPworker@@QAEHPAVcommPort@@@Z"));
    auto pilot = reinterpret_cast<Fn1>(Proc(worker, "?sendPilotSequence@FZAPworker@@QAEHXZ"));
    auto connect = reinterpret_cast<FnU16>(Proc(worker, "?connectToDevice@FZAPworker@@QAEHG@Z"));
    auto bootmode = reinterpret_cast<Fn1>(Proc(worker, "?enterBootmode@FZAPworker@@QAEHXZ"));
    auto unlock = reinterpret_cast<Fn1>(Proc(worker, "?UnLock@FZAPworker@@QAEHXZ"));
    auto read = reinterpret_cast<FnRead>(Proc(worker, "?readMemory@FZAPworker@@QAEHPAEII@Z"));
    if (!rsCtor || !rsOpen || !rsBaud || !fzCtor || !fzInit || !pilot || !connect ||
        !bootmode || !read) {
        return 2;
    }

    // The vendor classes are not exposed through headers. Reserve comfortably
    // larger storage than the constructors touch.
    std::vector<uint8_t> portObj(4096, 0);
    std::vector<uint8_t> workerObj(65536, 0);
    rsCtor(portObj.data(), portName.c_str());
    const int opened = rsOpen(portObj.data());
    std::printf("open(%s)=%d\n", portName.c_str(), opened);
    // FlashZap RS232Port::openPort uses 0 for success.
    std::printf("baud=%d\n", rsBaud(portObj.data(), baud));

    fzCtor(workerObj.data());
    const int init = fzInit(workerObj.data(), portObj.data());
    std::printf("FZAPinit=%d\n", init);
    if (init != 0) return 3;

    std::printf("pilot=%d\n", pilot(workerObj.data()));
    std::printf("connect=%d\n", connect(workerObj.data(), 0));
    std::printf("enterBootmode=%d\n", bootmode(workerObj.data()));
    Sleep(1000);
    std::printf("unlock=%d\n", unlock ? unlock(workerObj.data()) : -1);
    Sleep(500);

    std::vector<uint8_t> image(length, 0);
    const uint32_t end = start + length - 1;
    const int result = read(workerObj.data(), image.data(), start, end);
    std::printf("readMemory(0x%08X..0x%08X)=%d\n", start, end, result);
    if (result != 0) return 4;

    WriteFileBytes(out + ".bin", image);
    WriteSrec(out, image, start);
    std::printf("wrote %s.bin and %s\n", out.c_str(), out.c_str());
    return 0;
}
