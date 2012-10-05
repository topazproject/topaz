def make_string_packer(padding=" ", nullterminated=False):
    def pack_string(packer, width):
        space = packer.space
        string = space.str_w(
            space.convert_type(packer.args_w[packer.args_index], space.w_string, "to_str")
        )
        if nullterminated:
            packer.result += string
            packer.result.append("\0")
        else:
            assert width >= 0
            string = string[:width]
            packer.result += string
            packer.result.extend([padding] * (width - len(string)))
        packer.args_index += 1
    return pack_string
