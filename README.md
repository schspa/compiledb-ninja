# compiledb-ninja

## used for generate compile_commands.json for emacs, vscode and so on.

```bash
[schspa@Arch-Schspa aosp]$ source build/envsetup.sh
[schspa@Arch-Schspa aosp]$ lunch aosp_arm64-eng
[schspa@Arch-Schspa aosp]$ make -j8
[schspa@Arch-Schspa aosp]$ # wait for a full build
[schspa@Arch-Schspa aosp]$ python ~/work/src/compiledb-ninja/compiledb-ninja.py -p out/build-aosp_arm64.ninja
[schspa@Arch-Schspa aosp]$ ls -al compile_commands.json
-rw-r--r-- 1 schspa schspa 59413087 May 20 14:57 compile_commands.json
```
![image](https://raw.githubusercontent.com/schspa/compiledb-ninja/master/pic/auto-complete.gif)
