
#### Why the dockerfile doesn't download godot binary automatically?

Because I hate when I try to use one of those docker images but they are x86_64 only. Godot is fairly easy to build.
If you are on aarch64 like me (Raspberry Pi 4, oracle Ampere A1) this is how I build godot:
```bash
scons arch=arm64 platform=server target=release_debug use_llvm=no colored=yes pulseaudio=no CFLAGS="$CFLAGS -fPIC -Wl,-z,relro,-z,now"  CXXFLAGS="$CXXFLAGS -fPIC -Wl,-z,relro,-z,now" LINKFLAGS="$LDFLAGS"  -j4
strip bin/godot*
```

