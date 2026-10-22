# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2026 Northwestern University.
#
# invenio-subjects-mesh-common is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Download MeSH files."""

import requests


class RequestsDownloader:
    """Download engine using the requests library and aware of NLM quirks."""

    def download_file(self, url, dest_path):
        """Perform download and raise if issue."""
        with requests.get(url, stream=True) as resp:
            resp.raise_for_status()

            # NLM site doesn't return a 404 in some cases, but rather redirects
            # to an "Error page" so we have to check if such redirect happened
            # Unclear if this is an error on their part, so won't regression
            # test against it.
            if len(resp.history) != 0:
                location = resp.history[0].headers.get("Location")
                if location == "https://www.nlm.nih.gov/cgi/archive/error.cgi":
                    raise Exception(f"{url} doesn't exist.")

            with open(dest_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        return dest_path


class MeSHFileToDownload:
    """MeSH file to download."""

    def __init__(self, paths_remote, path_local, download_engine):
        """Constructor."""
        self.paths_remote = paths_remote
        self.path_local = path_local
        self.download_engine = download_engine
        self.base_url = "https://nlmpubs.nlm.nih.gov/projects/mesh"

    def get_url(self, path_remote):
        """Return url."""
        return self.base_url + "/" + path_remote

    def download(self, cache=False):
        """Try to fetch file by checking potential locations."""
        last_exception = None

        if cache and self.path_local.exists():
            return

        for path_remote in self.paths_remote:
            try:
                # Write to disk
                self.download_engine.download_file(
                    self.get_url(path_remote),
                    self.path_local,
                )
                return
            except Exception as e:
                print(f"Request failed: {e}")
                last_exception = e

        if last_exception:
            raise last_exception


class MeSHDownloader:
    """Download MeSH files."""

    def __init__(self, directory, year, cache=False, download_engine=None):
        """Constructor."""
        self.directory = directory
        self.year = str(year)
        self.cache = cache
        self.download_engine = download_engine
        self.file_for_terms = MeSHFileToDownload(
            paths_remote=[
                # The .gz file hosted on MeSH site is actually not a .gz,
                # so not using it for now. Re-visit later perhaps.
                f"{self.year}/xmlmesh/desc{self.year}.xml",
                f"MESH_FILES/xmlmesh/desc{self.year}.xml",
                f"MESH_FILES/mesh_browser/desc{self.year}.xml",
            ],
            path_local=self.directory / f"desc{self.year}.xml",
            download_engine=self.download_engine,
        )
        self.file_for_replace = MeSHFileToDownload(
            paths_remote=[
                f"{self.year}/newterms/replace{self.year}.txt",
                f"MESH_FILES/newterms/replace{self.year}.txt",
            ],
            path_local=self.directory / f"replace{self.year}.txt",
            download_engine=self.download_engine,
        )
        self.files_to_download = [
            self.file_for_terms,
            self.file_for_replace,
        ]

    def download(self):
        """Download MeSH files of interest."""
        for file_to_download in self.files_to_download:
            file_to_download.download(cache=self.cache)

    @property
    def terms_filepath(self):
        """Downloaded terms filepath."""
        return self.file_for_terms.path_local

    @property
    def replace_filepath(self):
        """Downloaded replace filepath."""
        return self.file_for_replace.path_local
