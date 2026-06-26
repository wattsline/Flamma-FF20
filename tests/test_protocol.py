from ff20.protocol import pack_command


def test_pack_version_command_prefix():
    assert pack_command(0, b"").startswith(bytes([0xAA, 0x55, 0x01, 0x00, 0x00]))


def test_pack_read_loop_page_length():
    p = pack_command(0x82, bytes([2, 0, 1, 0, 0, 0]))
    assert p[:5] == bytes([0xAA, 0x55, 0x07, 0x00, 0x82])
