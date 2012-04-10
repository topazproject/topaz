from rupypy.main import entry_point


def target(driver, args):
    driver.exe_name = "rupypy-c"
    return entry_point, None
