# -*- coding: utf-8 -*-

import os
import lzma
import lzham
import struct
import argparse

from PIL import Image
from Reader import BinaryReader


def convert_pixel(pixel, type):
    if type == 0 or type == 1:
        # RGB8888
        return struct.unpack('4B', pixel)

    elif type == 2:
        # RGB4444
        pixel, = struct.unpack('<H', pixel)
        return (((pixel >> 12) & 0xF) << 4, ((pixel >> 8) & 0xF) << 4,
                ((pixel >> 4) & 0xF) << 4, ((pixel >> 0) & 0xF) << 4)

    elif type == 3:
        # RBGA5551
        pixel, = struct.unpack('<H', pixel)
        return (((pixel >> 11) & 0x1F) << 3, ((pixel >> 6) & 0x1F) << 3,
                ((pixel >> 1) & 0x1F) << 3, ((pixel) & 0xFF) << 7)

    elif type == 4:
        # RGB565
        pixel, = struct.unpack("<H", pixel)
        return (((pixel >> 11) & 0x1F) << 3,
                ((pixel >> 5) & 0x3F) << 2, (pixel & 0x1F) << 3)

    elif type == 6:
        # LA88 = Luminance Alpha 88
        pixel, = struct.unpack("<H", pixel)
        return (pixel >> 8), (pixel >> 8), (pixel >> 8), (pixel & 0xFF)

    elif type == 10:
        # L8 = Luminance8
        pixel, = struct.unpack("<B", pixel)
        return pixel, pixel, pixel

    else:
        raise Exception("Unknown pixel type {}.".format(type))


def process(data, filename, decompress):
    picCount = 0

    if decompress:
        if data[:2] == b'SC':
            # Skip the header if there's any
            hash_length = int.from_bytes(data[6: 10], 'big')
            data = data[10 + hash_length:]

        if data[:4] == b'SCLZ':
            print('[*] Detected LZHAM compression !')

            dict_size = int.from_bytes(data[4:5], 'big')
            uncompressed_size = int.from_bytes(data[5:9], 'little')

            try:
                data = lzham.decompress(data[9:], uncompressed_size, {'dict_size_log2': dict_size})

            except Exception as exception:
                print('Cannot decompress {} !'.format(filename))
                return

        else:
            print('[*] Detected LZMA compression !')
            data = data[0:9] + (b'\x00' * 4) + data[9:]

            try:
                data = lzma.LZMADecompressor().decompress(data)

            except Exception as exception:
                print('Cannot decompress {} !'.format(filename))
                return

        print('[*] Successfully decompressed {} !'.format(filename))

    try:
        reader = BinaryReader(data)

        # Start reading binary stuff
        for i in range(6):
            reader.read_uint16()  # ShapeCount etc..

        reader.read(5)

        exportCount = reader.read_uint16()

        for i in range(exportCount):
            reader.read_int16()

        for i in range(exportCount):
            reader.read_string(reader.read_byte())

        while reader.peek():
            dataBlockTag = reader.read(1).hex()
            dataBlockSize = reader.read_uint32()

            if dataBlockTag == "18" or dataBlockTag == "01":
                if dataBlockSize > 5:
                    print("[*] Texture found")
                    read_texture(reader, filename, picCount)
                    picCount += 1

                else:
                    reader.read_byte()  # PixelType
                    reader.read_uint16()  # Width
                    reader.read_uint16()  # Height

            else:
                reader.read(dataBlockSize)

    except Exception as exception:
        print('[*] An error occured while reading ({}), maybe ur file is compressed. Try to re-run the script with the option -lzma'.format(exception.__class__.__name__))


def read_texture(reader, filename, picCount):

    pixelType = reader.read_byte()
    width = reader.read_uint16()
    height = reader.read_uint16()

    print("[INFO]: PixelFormat {}, Width {}, Height {}".format(pixelType, width, height))

    if pixelType in (0, 1):
        pixelSize = 4

    elif pixelType in (2, 3, 4, 6):
        pixelSize = 2

    elif pixelType == 10:
        pixelSize = 1

    else:
        raise Exception("Unknown pixel type {}.".format(pixelType))

    img = Image.new("RGBA", (width, height))
    pixels = []

    for y in range(width):
        for x in range(height):
            pixels.append(convert_pixel(reader.read(pixelSize), pixelType))

    img.putdata(pixels)
    img.save(filename.split('.')[0] + ('_' * picCount) + '.png', 'PNG')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Extract png files from old .sc files')
    parser.add_argument('files', help='.sc file(s)', nargs='+')
    parser.add_argument('-d', '--decompress', help='Try to decompress your file before processing it', action='store_true')

    args = parser.parse_args()

    for file in args.files:
        if file.endswith('.sc'):
            if os.path.isfile(file):
                with open(file, 'rb') as f:
                    process(f.read(), file, args.decompress)

            else:
                print('[*] File don\'t exist :/')

        else:

            print('[*] Only .sc are supported !')
