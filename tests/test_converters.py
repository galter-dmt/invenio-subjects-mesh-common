#
# Copyright (C) 2021-2026 Northwestern University.
#
# invenio-subjects-mesh-common is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test MeSH-related conversion functionality."""

from galter_subjects_utils.types_internal import Subject

from invenio_subjects_mesh_common.converters import (
    MeSHRDMConverter,
    MeSHToDeltasGeneratorReplacementsConverter,
)


def test_converter():
    internal_entries = [
        {
            "main_heading": "Seed Bank",
            "descriptor_class": "1",
            "allowed_qualifiers": [
                {"id": "Q000145", "main_heading": "classification"},
                {"id": "Q000191", "main_heading": "economics"},
            ],
            "id": "D000068098",
        },
    ]

    converter = MeSHRDMConverter(internal_entries)
    subjects = [s for s in converter.iter_rdm_subjects(qualified=True)]

    expected = [
        {
            "id": 'https://id.nlm.nih.gov/mesh/D000068098',
            "scheme": "MeSH",
            "subject": "Seed Bank"
        },
        {
            "id": 'https://id.nlm.nih.gov/mesh/D000068098Q000145',
            "scheme": "MeSH",
            "subject": "Seed Bank/classification"
        },
        {
            "id": 'https://id.nlm.nih.gov/mesh/D000068098Q000191',
            "scheme": "MeSH",
            "subject": "Seed Bank/economics"
        },
    ]
    assert expected == subjects


def test_mesh_to_deltas_generator_replacements_converter():
    # ids just need to be consistent here
    subject_far_east = Subject(id="D005202", scheme="MeSH", label="Far East")
    subject_asia_eastern = Subject(
        id="D005202",
        scheme="MeSH",
        label="Asia, Eastern",
    )
    subject_natives = Subject(
        id="D044467",
        scheme="MeSH",
        label="American Indians or Alaska Natives",
    )
    subject_native = Subject(
        id="D044467",
        scheme="MeSH",
        label="American Indian or Alaska Native",
    )
    subject_asians = Subject(id="D044466", scheme="MeSH", label="Asians")
    subject_asian_people = Subject(
        id="D044466",
        scheme="MeSH",
        label="Asian People",
    )

    subjects_pool_src = [subject_far_east, subject_natives, subject_asians]
    subjects_pool_dst = [
        subject_asia_eastern,
        subject_native,
        subject_asian_people,
    ]

    replacements_internal = [
        {
            "main_heading_old": "Far East",
            "main_heading_new": "Asia, Eastern",
            "delete": "",
            "status": "P",
        },
        {
            "main_heading_old": "American Indians or Alaska Natives",
            "main_heading_new": "American Indian or Alaska Native",
            "delete": "#",
            "status": "P",
        },
        {
            "main_heading_old": "Asians",
            "main_heading_new": "Asian People",
            "delete": "",
            "status": "N*",
        },
        # These two will not show up in final replacements dict
        {
            "main_heading_old": "Unknown source",
            "main_heading_new": "Asian People",
            "delete": "",
            "status": "N*",
        },
        {
            "main_heading_old": "Asians",
            "main_heading_new": "Unknown destination",
            "delete": "",
            "status": "N*",
        },
    ]

    converter = MeSHToDeltasGeneratorReplacementsConverter(
        replacements_internal, subjects_pool_src, subjects_pool_dst,
    )
    result = converter.convert()

    expected = {
        subject_far_east: subject_asia_eastern,
        subject_natives: subject_native,
        subject_asians: subject_asian_people,
    }
    assert expected == result
