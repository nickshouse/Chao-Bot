import struct
import sys

EXPECTED_SIZE = 2112

def read_file(filename):
    with open(filename, 'rb') as file:
        return file.read()

def convert_to_chao_struct(data):
    num_elements = EXPECTED_SIZE // 2  # Number of 2-byte elements
    chao_format = 'H' * num_elements   # Format string for 2-byte unsigned integers
    return struct.unpack(chao_format, data[:EXPECTED_SIZE])

def write_to_file(chao_data, output_filename):
    with open(output_filename, 'w') as file:
        file.write(', '.join(map(str, chao_data)))

def main(input_filename, output_filename):
    data = read_file(input_filename)
    chao_data = convert_to_chao_struct(data)
    write_to_file(chao_data, output_filename)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_filename> <output_filename>", file=sys.stderr)
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    main(input_filename, output_filename)
