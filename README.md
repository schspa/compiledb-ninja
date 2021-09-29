# compiledb-ninja

## Introduction

Used for generating compile_commands.json for instructing IDE plugins (emacs, vscode, clangd...) how to compile a ninja project.

Tested working on the Ninja file produced by AOSP 7.1 r57. 

```bash
source build/envsetup.sh
# Lunch any configuration you need
lunch aosp_arm64-eng
# Can stop making as long as ninja file is created
make -j8
# Use a proper number of processes
python ./compiledb-ninja.py -p out/build-aosp_arm64.ninja -j 4
# Enjoy your compile_commands.json
ls -al compile_commands.json
```
