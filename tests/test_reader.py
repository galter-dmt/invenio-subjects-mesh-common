# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2026 Northwestern University.
#
# invenio-subjects-mesh-common is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test MeSH-related reading functionality."""

from pathlib import Path

from invenio_subjects_mesh_common.reader import (
    MeSHNewReader,
    MeSHReplaceReader,
    MeSHXMLReader,
    topic_filter_xml,
)

# Utilities


def assert_includes(dicts, dict_cores):
    """Checks that each dict in dicts has the corresponding dict_core."""
    for d, dc in zip(dicts, dict_cores):
        for key, value in dc.items():
            assert value == d[key]

# Tests


def test_reader_descriptors_filter():
    filepath = Path(__file__).parent / "data" / "fake_desc2022.xml"

    reader = MeSHXMLReader(filepath, filter=topic_filter_xml)
    topics = [t for t in reader.iter_internal_entries()]

    expected_cores = [
        {
            "main_heading": "Seed Bank",
            "descriptor_class": "1",
            "allowed_qualifiers": [
                {"id": "Q000145", "main_heading": "classification"},
                {"id": "Q000191", "main_heading": "economics"},
                {"id": "Q000266", "main_heading": "history"},
                {"id": "Q000331", "main_heading": "legislation & jurisprudence"},  # noqa
                {"id": "Q000458", "main_heading": "organization & administration"},  # noqa
                {"id": "Q000592", "main_heading": "standards"},
                {"id": "Q000600", "main_heading": "supply & distribution"},
                {"id": "Q000639", "main_heading": "trends"},
                {"id": "Q000706", "main_heading": "statistics & numerical data"},  # noqa
                {"id": "Q000941", "main_heading": "ethics"},
            ],
            "id": "D000068098",
        },
        {
            "main_heading": "Abbreviations as Topic",
            "descriptor_class": "1",
            "id": "D000004",
        },
        {
            "main_heading": "Abdomen",
            "descriptor_class": "1",
            "allowed_qualifiers": [
                {"id": "Q000002", "main_heading": "abnormalities"},
                {"id": "Q000033", "main_heading": "anatomy & histology"},
                {"id": "Q000098", "main_heading": "blood supply"},
                {"id": "Q000196", "main_heading": "embryology"},
                {"id": "Q000254", "main_heading": "growth & development"},
                {"id": "Q000294", "main_heading": "innervation"},
                {"id": "Q000382", "main_heading": "microbiology"},
                {"id": "Q000469", "main_heading": "parasitology"},
                {"id": "Q000473", "main_heading": "pathology"},
                {"id": "Q000502", "main_heading": "physiology"},
                {"id": "Q000503", "main_heading": "physiopathology"},
                {"id": "Q000528", "main_heading": "radiation effects"},
                {"id": "Q000601", "main_heading": "surgery"},
                {"id": "Q000821", "main_heading": "virology"},
                {"id": "Q000000981", "main_heading": "diagnostic imaging"},
            ],
            "id": "D000005",
        },
        {
            "main_heading": "American Indians or Alaska Natives",
            "descriptor_class": "1",
            "allowed_qualifiers": [
                {"id": "Q000145", "main_heading": "classification"},
                {"id": "Q000193", "main_heading": "education"},
                {"id": "Q000266", "main_heading": "history"},
                {"id": "Q000331", "main_heading": "legislation & jurisprudence"},  # noqa
                {"id": "Q000523", "main_heading": "psychology"},
                {"id": "Q000706", "main_heading": "statistics & numerical data"},  # noqa
                {"id": "Q000208", "main_heading": "ethnology"},
                {"id": "Q000235", "main_heading": "genetics"},
            ],
            "id": "D000086562",
        },
    ]
    assert_includes(topics, expected_cores)


# def test_reader_qualifiers():
#     filepath = Path(__file__).parent / "data" / "fake_q2023.bin"

#     reader = MeSHReader(filepath)
#     qualifiers = [q for q in reader]

#     expected_cores = [
#         {
#             "QA": "AB",
#             "SH": "abnormalities",
#             "UI": "Q000002"
#         },
#         {
#             "QA": "AH",
#             "SH": "anatomy & histology",
#             "UI": "Q000033"
#         },
#         {
#             "QA": "CL",
#             "SH": "classification",
#             "UI": "Q000145"
#         },
#         {
#             "QA": "EC",
#             "SH": "economics",
#             "UI": "Q000191"
#         },
#     ]
#     assert_includes(qualifiers, expected_cores)


def test_new_reader():
    filepath = Path(__file__).parent / "data" / "fake_meshnew2023.txt"

    reader = MeSHNewReader(filepath)
    entries = [e for e in reader.read()]

    expected = [
        {
            "MH": "Document Analysis",
            "UI": "D000092002",
            "MN": "H1.770.644.241.850.375",
            "MS": "A form of qualitative research that uses a systematic procedure to analyze documentary evidence and answer specific research questions.",  # noqa
            "HN": "2023",
        },
        {
            "MH": "Family Structure",
            "UI": "D000092822",
            "MN": "F1.829.263.315.250",
            "MN": "I1.240.361.330",
            "MN": "I1.880.761.125",
            "MN": "I1.880.853.150.423.250",
            "MN": "N1.224.361.330",
            "MN": "N1.824.308.125",
            "MN": "N6.850.505.400.400.580",
            "MS": "Structural nature of relationships among members of a household typically in reference to a MINOR residing in the same home. More broadly any organizational framework that determines family membership, and the functions and hierarchical position of family members (https://eric.ed.gov/?qt=Family+Structure&ti=Family+Structure).",  # noqa
            "HN": "2023; for STEPFAMILY and FAMILY, RECONSTITUTED use FAMILY 1996-2022; for MATRIARCHY and PATRIARCHY use FAMILY CHARACTERISTICS 1995-2022",  # noqa
            "BX": "Family, Reconstituted",
            "BX": "Reconstituted Family",
            "BX": "Step-parent Family",
            "BX": "Stepfamily",
            "BX": "Stepparent Family",
        }
    ]
    assert expected == entries


def test_replace_reader():
    filepath = Path(__file__).parent / "data" / "fake_replace2023.txt"

    reader = MeSHReplaceReader(filepath)
    entries = [e for e in reader.read()]

    expected = [
        {
            "MH OLD": "Far East",
            "MH NEW": "Asia, Eastern",
            "delete": "",
            "status": "P",
        },
        {
            "MH OLD": "American Indians or Alaska Natives",
            "MH NEW": "American Indian or Alaska Native",
            "delete": "#",
            "status": "P",
        },
        {
            "MH OLD": "Asians",
            "MH NEW": "Asian People",
            "delete": "",
            "status": "N*",
        },
        {
            "MH OLD": "Whites",
            "MH NEW": "White People",
            "delete": "",
            "status": "P*",
        },
        {
            "MH OLD": "RNA, Guide",
            "MH NEW": "RNA, Guide, Kinetoplastida",
            "delete": "",
            "status": "",
        }
    ]
    assert expected == entries
