---
title: Decrypting IL2CPP Metadata
category: General
---

> The final code to decrypt and unshuffle the header is available [here]({{ site.data.urls.repository }}/tree/master/src/decrypt-metadata)

Since version 4.0.2.0.0 (26th September 2023) the game has started encrypted the header of the IL2CPP global metadata.
The obfuscator they are using is [Mfuscator](https://assetstore.unity.com/packages/tools/utilities/mfuscator-il2cpp-encryption-256631#description) on the Unity store.
Thankfully for us, this metadata can easily be deobufscated.

To start, let's look at what the IL2CPP metadata contains.
> From [Il2CppDumper/Il2Cpp/MetadataClass.cs](https://github.com/Perfare/Il2CppDumper/blob/217f1d4737cd9d9d16ab5bef355156bcbc44f9e0/Il2CppDumper/Il2Cpp/MetadataClass.cs)

```cs
public sealed class Metadata : BinaryStream
{
    public Il2CppGlobalMetadataHeader header;
    ...

public class Il2CppGlobalMetadataHeader
{
    public uint sanity;
    public int version;
    public uint stringLiteralOffset; // string data for managed code
    public int stringLiteralSize;
    public uint stringLiteralDataOffset;
    public int stringLiteralDataSize;
    public uint stringOffset; // string data for metadata
    public int stringSize;
    public uint eventsOffset; // Il2CppEventDefinition
    public int eventsSize;
    public uint propertiesOffset; // Il2CppPropertyDefinition
    public int propertiesSize;
    public uint methodsOffset; // Il2CppMethodDefinition
    public int methodsSize;
    ...
```

From this, we can see that `global-metadata.dat` begins with a header that starts with two constants: `sanity` and `version`.
Specifically, all metadata files should start with 4 sanity bytes (either `FAB11BAF` or `AF1BB1FA` depending on endianness) to verify that the metadata is valid. At the time of writing this, the metadata version is 29.
The remaining data in the header is for the offset and size of each segment of the metadata.

Opening our `global-metadata.dat` file in a hex editor (such as [ImHex](https://github.com/WerWolv/ImHex)) we can see that this isn't the case. Rather, our metadata header begins with the string `"In the beginning God created the heavens and the earth."`
![Screenshot]({{ "/files/images/posts/decrypting-il2cpp-metadata/encrypted_metadata_hex.png" | relative_url }})

We've now determined that this metadata file is most likely encrypted. The next step is to open the GameAssembly.dll in IDA Pro and reverse the logic used to decrypt the header. The following resource is extremely useful and go into a lot of detail on how to begin this [https://katyscode.wordpress.com/2021/02/23/il2cpp-finding-obfuscated-global-metadata/](https://katyscode.wordpress.com/2021/02/23/il2cpp-finding-obfuscated-global-metadata/)

## Decrypting
Using the above resources, we know we have to find the `void* il2cpp::vm::MetadataLoader::LoadMetadataFile(const char* fileName)` function.
A shortcut to find this function is to searching for the string literal "Metadata".
![Screenshot]({{ "/files/images/posts/decrypting-il2cpp-metadata/load_metadata_into_memory.png" | relative_url }})

^ This function loads the metadata file into memory. XRefing this function we arrive at the modified `LoadMetadataFile` function. The first section of this function is as follows.
![Screenshot]({{ "/files/images/posts/decrypting-il2cpp-metadata/xor_metadata_dat.png" | relative_url }})
All this code does is XOR `D1DAD9D4D7DA9BDBD3C2D7D2D7C2D798D2D7C2` with they key `0xB6`. Which results in the string `"global-metadata.dat"`, the filename of our metadata.

The next section of code:
![Screenshot]({{ "/files/images/posts/decrypting-il2cpp-metadata/metadata_xxtea_key.png" | relative_url }})
There's a couple things going on here.
The first thing sticking out is this string `"##%$vsw'lytyqlusxul##p\"lvxrsv\"y\"y'xu%tv\"qsy\"l%%#qlux'ul# wylys\"t 'v$us''A"` is XOR'd with the key `0x41`. The output of this is `"bbde726f-8580-4294-bb1c-79327c8c8f94d57c028c-ddb0-49f4-ba68-82c5af7e42ff"`.
This is the key that is used to decrypt the header.

To determine the cipher used, we can use the IDA Pro plugin [findcrypt-yara](https://github.com/polymorf/findcrypt-yara)
![Screenshot]({{ "/files/images/posts/decrypting-il2cpp-metadata/metadata_findcrypt_results.png" | relative_url }})
We can see the first result here is the xxtea cipher. Note that xxtea requires a key length of 16 bytes, which is taken from the last 16 bytes of the key that was deciphered earlier.


## Unshuffling
After decrypting the header we get the following:
![Screenshot]({{ "/files/images/posts/decrypting-il2cpp-metadata/decrypted_header.png" | relative_url }})

Remember earlier, we noted that the IL2CPP header should begin with two constants: `sanity` and `version`?
We can see these do exist in the header, meaning we did successfully decrypted the header.
However, it appears the header has been shuffled, randomly placing all the bytes in different positions. 

So how should we go about unshuffling the header? We need to:
1. Determine which integer is an offset
2. Determine which integer is a size
3. Determine the pairs of offsets and their size

The theory to solving this is that the metadata sections are contiguous, without any gaps or padding between each other. Additionally, the offsets are in ascending order (the same order they appear in the metadata).
What this means, is that given a section's offset and size, the next offset will begin at the end of the previous offset (offset + size == next offset)

For example, (here is an unshuffled header):
![Screenshot]({{ "/files/images/posts/decrypting-il2cpp-metadata/next_offset.png" | relative_url }})

We can see the first offset is `1088` and the size `131720`. That means the next offset must be `1088 + 131720 = 132808` which we can see this is the case.

And that is all it takes to unobfuscate the IL2CPP header!
The final code to decrypt and unshuffle the header is available [here]({{ site.data.urls.repository }}/tree/master/src/decrypt-metadata)