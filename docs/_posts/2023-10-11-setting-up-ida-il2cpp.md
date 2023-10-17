---
title: Setting up IDA + Dumping IL2CPP
category: General
---

## Background Info
* RotMG is written in Unity (C#)
* Uses the IL2CPP scripting backend which converts C#’s intermediate language to C++.

What this means for us is reverse engineering the game is not as easy as simply drag and dropping the game’s DLL into any .NET Decompiler, like you would with other non IL2CPP’d games.
Instead we have to use a dissassembler such as IDA or Ghidra.
You should use the Pro version of idea as it supports IDAPython, which will use to recover symbols and structs from the IL2CPP metadata.

Useful IL2CPP information:
+ [https://katyscode.wordpress.com/category/reverse-engineering/il2cpp](https://katyscode.wordpress.com/category/reverse-engineering/il2cpp)

## Dissassembly
First, find the game’s assembly located in: `Documents\RealmOfTheMadGod\Production\GameAssembly.dll`.
To make things easier copy the file into a separate folder. Then load the file into IDA and wait for analysis to finish (wait for the bottom left to say “AU: idle”)

In the mean time, we will use [Il2CppDumper](https://github.com/Perfare/Il2CppDumper). Copy the the following file into your working directory `Documents\RealmOfTheMadGod\Production\RotMG Exalt_Data\il2cpp_data\Metadata\global-metadata.dat`

Since version 4.0.2.0.0 (26th September 2023) the game has started obfuscating the header of the IL2CPP global metadata.
We can fix this by using the following script: [decrypt-metadata]({{ site.data.urls.repository }}/tree/master/src/decrypt-metadata).
If you're interested, you can read how deobfuscation was accomplished [here]({% post_url 2023-10-12-decrypting-il2cpp-metadata %}).

After decrypting the metadata, we can now run Il2CppDumper:
`Il2CppDumper.exe GameAssembly.dll global-metadata-fixed.dat il2cpp_out/`

After IDA is done loading, we can run the `ida_with_struct_py3.py` file by clicking `File -> Script File` in IDA and selecting the outputted `script.json` and `il2cpp.h` files.

Done! We now have a disassembled game with recovered symbols and structs

![Screenshot]({{ "/files/images/posts/rename/ida64_nC9IbaOOxy.png" | relative_url }})