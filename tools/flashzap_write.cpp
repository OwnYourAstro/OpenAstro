// Load a raw payload into target RAM through the FlashZap worker API.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
using Fn1 = int(__thiscall*)(void*);
using FnU16 = int(__thiscall*)(void*, uint16_t);
using FnU32 = int(__thiscall*)(void*, uint32_t);
using FnInit = int(__thiscall*)(void*, void*);
using FnCtorStr = void(__thiscall*)(void*, const char*);
using FnCtorVoid = void(__thiscall*)(void*);
using FnMem = int(__thiscall*)(void*, uint8_t*, uint32_t, uint32_t);
using FnJump = int(__thiscall*)(void*, uint32_t);
static void* Proc(HMODULE m,const char*n){auto p=GetProcAddress(m,n);if(!p)std::printf("missing %s\n",n);return (void*)p;}
int main(int argc,char**argv){
 if(argc<5){std::printf("usage: flashzap_write <dir> <COMx> <payload.bin> <start> [baud]\n");return 2;}
 std::string dir=argv[1], port=argv[2]; uint32_t start=(uint32_t)strtoul(argv[4],nullptr,0); uint32_t baud=argc>=6?(uint32_t)strtoul(argv[5],nullptr,0):115200;
 std::ifstream f(argv[3],std::ios::binary); std::vector<uint8_t> data((std::istreambuf_iterator<char>(f)),{});
 if(data.empty()){std::printf("empty payload\n");return 3;}
 SetDllDirectoryA(dir.c_str()); HMODULE com=LoadLibraryA((dir+"\\fzap_com.dll").c_str()), worker=LoadLibraryA((dir+"\\fzap_worker.dll").c_str());
 if(!com||!worker){std::printf("dll load failed %lu\n",GetLastError());return 4;}
 auto rsCtor=(FnCtorStr)Proc(com,"??0RS232Port@@QAE@PBD@Z"); auto rsOpen=(Fn1)Proc(com,"?openPort@RS232Port@@UAEHXZ"); auto rsBaud=(FnU32)Proc(com,"?changeBaudRate@RS232Port@@UAEHI@Z");
 auto fzCtor=(FnCtorVoid)Proc(worker,"??0FZAPworker@@QAE@XZ"); auto fzInit=(FnInit)Proc(worker,"?FZAPinit@FZAPworker@@QAEHPAVcommPort@@@Z");
 auto pilot=(Fn1)Proc(worker,"?sendPilotSequence@FZAPworker@@QAEHXZ"); auto connect=(FnU16)Proc(worker,"?connectToDevice@FZAPworker@@QAEHG@Z");
 auto bootmode=(Fn1)Proc(worker,"?enterBootmode@FZAPworker@@QAEHXZ"); auto unlock=(Fn1)Proc(worker,"?UnLock@FZAPworker@@QAEHXZ");
 auto writeMem=(FnMem)Proc(worker,"?writeMemory@FZAPworker@@QAEHPAEII@Z"); auto readMem=(FnMem)Proc(worker,"?readMemory@FZAPworker@@QAEHPAEII@Z"); auto jump=(FnJump)Proc(worker,"?jump@FZAPworker@@QAEHI@Z");
 if(!rsCtor||!rsOpen||!rsBaud||!fzCtor||!fzInit||!pilot||!connect||!bootmode||!unlock||!writeMem||!readMem||!jump)return 5;
 std::vector<uint8_t> pobj(4096,0), wobj(65536,0); rsCtor(pobj.data(),port.c_str()); std::printf("open=%d\n",rsOpen(pobj.data())); std::fflush(stdout); rsBaud(pobj.data(),baud);
 fzCtor(wobj.data()); const int init=fzInit(wobj.data(),pobj.data()); std::printf("init=%d\n",init); std::fflush(stdout);
 const int pil=pilot(wobj.data()); std::printf("pilot=%d\n",pil); std::fflush(stdout);
 const int con=connect(wobj.data(),0); std::printf("connect=%d\n",con); std::fflush(stdout);
 const int bm=bootmode(wobj.data()); std::printf("boot=%d\n",bm); std::fflush(stdout);
 const int ul=unlock(wobj.data()); std::printf("unlock=%d\n",ul); std::fflush(stdout);
 uint32_t end=start+(uint32_t)data.size()-1; int wr=writeMem(wobj.data(),data.data(),start,(uint32_t)data.size()); std::printf("write(%08X len=%u)=%d\n",start,(unsigned)data.size(),wr); std::fflush(stdout);
 std::vector<uint8_t> check(data.size(),0); int rr=readMem(wobj.data(),check.data(),start,end); std::printf("read=%d match=%d\n",rr,(int)(check==data)); std::fflush(stdout);
 if(wr==0&&rr==0&&check==data){ if (GetEnvironmentVariableA("SKIP_JUMP",nullptr,0)) { std::printf("jump skipped\n"); return 0; } std::printf("jump=%d\n",jump(wobj.data(),start)); std::fflush(stdout); return 0;} return 6;
}
