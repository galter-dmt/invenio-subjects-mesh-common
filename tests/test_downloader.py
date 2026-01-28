# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2026 Northwestern University.
#
# invenio-subjects-mesh-common is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test MeSH-related download functionality."""

import shutil
from pathlib import Path

from invenio_subjects_mesh_common.downloader import MeSHDownloader

# Helpers


class FakeRequestsDownloader:
    """Fake downloader."""

    def __init__(self):
        """Constructor."""

    def download_file(self, url, dest_path):
        # It pretends that the d2023.bin is not in
        # f"{self.year}/asciimesh/d{self.year}.bin" or
        # f"MESH_FILES/asciimesh/d{self.year}.bin"
        urls_invalid = [
            "https://nlmpubs.nlm.nih.gov/projects/mesh/2023/asciimesh/d2023.bin",  # noqa
            "https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/asciimesh/d2023.bin",  # noqa
        ]
        if url in urls_invalid:
            raise Exception(f"{url} doesn't exist.")

        filename = url.rsplit("/", 1)[-1]
        fp = Path(__file__).parent / f"data/fake_{filename}"
        shutil.copyfile(fp, dest_path)

        return dest_path


# Tests


def test_downloader(tmp_path):
    # Tests high level interfaces i.e., we have the right names, interfaces and
    # final files written to disk.
    # Full network and internals test done manually.
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir()

    downloader = MeSHDownloader(
        year="2023",
        directory=downloads_dir,
        download_engine=FakeRequestsDownloader(),
    )
    downloader.download()

    assert (downloads_dir / "d2023.bin").exists()
    assert (downloads_dir / "q2023.bin").exists()
    assert (downloads_dir / "meshnew2023.txt").exists()
    assert (downloads_dir / "replace2023.txt").exists()
