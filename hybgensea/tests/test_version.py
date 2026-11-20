from importlib.metadata import version

import hybgensea


def test_version_matches_metadata():
    # The version file is generated at build time; a wheel without it would fail to import.
    assert hybgensea.__version__ == version("hybgensea")
