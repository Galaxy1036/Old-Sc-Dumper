# -*- coding: utf-8 -*-

import os
import sys
import lzma
import struct
import argparse

from PIL import Image
from io import BytesIO
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
        return (((pixel >> 11) & 0x1F) << 3, ((pixel >> 5) & 0x3F) << 2, (pixel & 0x1F) << 3)
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


def process(Data, filename, useLzma):
    picCount = 0

    if useLzma:
        data = Data[26:]
        data = data[0:9] + (b'\x00' * 4) + data[9:]
        try:
            data = lzma.LZMADecompressor().decompress(data)
            print('[*] Successfully decompressed using latest format')
        except _lzma.LZMAError:
            data = Data[0:9] + (b'\x00' * 4) + Data[9:]

            try:

                data = lzma.LZMADecompressor().decompress(data)
                print('[*] Successfully decompressed using old format')

            except _lzma.LZMAError:

                print('[*] Decompression failed !')
                sys.exit()

    try:
        Reader = BinaryReader(BytesIO(data))
        # Start reading binary stuff
        for i in range(6):
            Reader.read_uint16()  # ShapeCount etc..

        Reader.read(5)

        ExportCount = Reader.read_uint16()

        for i in range(ExportCount):
            Reader.read_int16()

        for i in range(ExportCount):
            Length = Reader.read_byte()
            Reader.read_string(Length)

        while Reader.peek():

            DataBlockTag = Reader.read(1).hex()
            DataBlockSize = Reader.read_uint32()

            if DataBlockTag == "18" or DataBlockTag == "01":

                if DataBlockSize > 5:
                    print("[*] Texture founded")
                    read_texture(Reader, filename, picCount)
                    picCount += 1

                else:
                    Reader.read_byte()  # PixelType
                    Reader.read_uint16()  # Width
                    Reader.read_uint16()  # Height

            else:
                Reader.read(DataBlockSize)

    except:
        print('[*] An error occured while reading, maybe ur file is compressed. Try to re-run the script with the option -lzma')


def read_texture(Reader, filename, picCount):

    PixelType = Reader.read_byte()
    Width = Reader.read_uint16()
    Height = Reader.read_uint16()

    print("[INFO]: PixelFormat {}, Width {}, Height {}".format(PixelType, Width, Height))

    if PixelType == 0 or PixelType == 1:
        pixelSize = 4
    elif PixelType == 2 or PixelType == 3 or PixelType == 4 or PixelType == 6:
        pixelSize = 2
    elif PixelType == 10:
        pixelSize = 1
    else:
        raise Exception("Unknown pixel type {}.".format(PixelType))

    img = Image.new("RGBA", (Width, Height))
    pixels = []

    for y in range(Width):
        for x in range(Height):
            pixels.append(convert_pixel(Reader.read(pixelSize), PixelType))

    img.putdata(pixels)
    img.save(filename.split('.')[0] + ('_' * picCount) + '.png', 'PNG')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Extract png files from old .sc files')
    parser.add_argument('files', help='.sc file(s)', nargs='+')
    parser.add_argument('-lzma', help='Include lzma decompression', action='store_true')

    args = parser.parse_args()

    for file in args.files:
        if file.endswith('.sc'):
            if os.path.exists(file):
                with open(file, 'rb') as f:
                    process(f.read(), file, args.lzma)

            else:
                print('[*] File don\'t exist :/')

        else:

            print('[*] Only .sc are supported !')
