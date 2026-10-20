# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 Northwestern University.
#
# invenio-subjects-mesh-common is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test MeSH-related conversion functionality."""

from invenio_subjects_mesh_common.converter import MeSHRDMConverter


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
        }
    ]
    # qualifiers_mapping = {
    #     "CL": {
    #         "QA": "CL",
    #         "SH": "classification",
    #         "UI": "Q000145"
    #     },
    #     "EC": {
    #         "QA": "EC",
    #         "SH": "economics",
    #         "UI": "Q000191"
    #     }
    # }

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
