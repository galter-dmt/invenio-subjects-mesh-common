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


class MeSHToDeltasGeneratorReplacementsConverter:
    """Convert internal MeSH replacement entries into RDM replacement dict."""

    def __init__(
        self,
        mesh_replacements,
        subjects_pool_src,
        subjects_pool_dst,
    ):
        """Constructor.

        Args:
            mesh_replacements (iterable[dict - replacement shape]) :
                MeSH replacment internal entries
            subjects_pool_src (iter[Subject]) : source of Subjects for replacement src
            subjects_pool_dst (iter[Subject]) : source of Subjects for replacement dst
        """  # noqa
        self._mesh_replacements = list(mesh_replacements)  # small so fit in memory  # noqa
        self._subjects_pool_src = subjects_pool_src
        self._subjects_pool_dst = subjects_pool_dst

    def convert(self):
        """Returns the full replacement dict.

        Returns:
            dict[Subject, Subject] : subject to subject replacement dict
        """
        # Src label to subject
        labels_for_src = [
            r["main_heading_old"] for r in self._mesh_replacements
        ]
        label_to_subject_src = {
            subject.label: subject
            for subject in self._subjects_pool_src
            if subject.label in labels_for_src
        }

        # Dst label to subject
        labels_for_dst = [
            r["main_heading_new"] for r in self._mesh_replacements
        ]
        label_to_subject_dst = {
            subject.label: subject
            for subject in self._subjects_pool_dst
            if subject.label in labels_for_dst
        }

        return {
            label_to_subject_src[r["main_heading_old"]]:
                label_to_subject_dst[r["main_heading_new"]]
            for r in self._mesh_replacements
            if (
                r["main_heading_old"] in label_to_subject_src and
                r["main_heading_new"] in label_to_subject_dst
            )
        }
