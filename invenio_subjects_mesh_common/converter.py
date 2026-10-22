# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2026 Northwestern University.
#
# invenio-subjects-mesh-common is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Convert MeSH data to InvenioRDM/ops."""

from .scheme import MeSHScheme


class MeSHRDMConverter:
    """Convert internal MeSH entries into RDM subject dicts."""

    def __init__(self, internal_entries):
        """Constructor.

        :param internal_entries: iterable[dict] - MeSH internal entries
        """
        self.internal_entries = internal_entries
        self.mesh = MeSHScheme()

    def iter_rdm_subjects(self, qualified=False):
        """Iterator over converted entries.

        :param qualified: bool - produce qualified entries as well
        """
        for entry in self.internal_entries:
            yield {
                "id": self.mesh.generate_id(entry["id"]),
                "scheme": self.mesh.name,
                "subject": entry["main_heading"],
            }

            if not qualified:
                continue

            for qualifier in entry.get("allowed_qualifiers", []):
                yield {
                    "id": self.mesh.generate_id(entry["id"] + qualifier["id"]),
                    "scheme": self.mesh.name,
                    "subject": entry["main_heading"] + "/" + qualifier["main_heading"]  # noqa
                }


class MeSHRDMReplaceConverter:
    """Convert internal MeSH replacement entries into RDM replacement dict."""

    def __init__(self, internal_entries):
        """Constructor.

        :param internal_entries: iterable[dict] - MeSH replacment internal
                                                  entries
        """
        self.internal_entries = internal_entries

    def convert(self):
        """Returns the full replacement dict."""
        return {
            e["main_heading_old"]: e["main_heading_new"]
            for e in self.internal_entries
        }
