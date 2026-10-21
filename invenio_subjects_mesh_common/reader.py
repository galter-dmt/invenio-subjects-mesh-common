# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 Northwestern University.
#
# invenio-subjects-mesh-common is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Read MeSH files."""

import re
import warnings

from lxml import etree

# Utilities


def topic_filter(record):
    """Filters for topical terms."""
    return record["descriptor_class"] == "1"


# Readers


class MeSHReader:
    """MeSH Reader."""

    def __init__(self, filepath, filter=lambda r: True):
        """Constructor."""
        self._filepath = filepath
        self._filter = filter

    def __iter__(self):
        """Iterate over terms.

        Deprecated.
        """
        yield from self.read()

    def read(self):
        """Alias for __iter__ (for now)."""
        with open(self._filepath, 'r') as f:
            record = {}

            for line in f:
                if "=" not in line:
                    continue

                key, value = [p.strip() for p in line.split("=", maxsplit=1)]
                self.update_record(record, key, value)

                # Assumes always ends with UI
                if key == "UI":
                    if self._filter(record):
                        yield record
                    record = {}

    def update_record(cls, record, key, value):
        """Update the value of a key in the MeSH record.

        We deal with special cases of interest here.
        """
        if key == "AQ":
            record[key] = [q.strip() for q in value.split()]
        else:
            record[key] = value


class MeSHNewReader:
    """Parser for MeSH new file."""

    def __init__(self, filepath):
        """Constructor."""
        self.filepath = filepath

    def read(self):
        """Read iteratively 'meshnew' file.

        This is a very simple parser that takes advantage of the
        structure of 'meshnew' files.

        Design:
        - lazy load file to reduce memory footprint during read
        """
        with open(self.filepath, 'r') as f:
            entry = {}
            for line in f:
                line = line.strip()
                # partition always yields 3-tuple, values may be '' though
                lv, dash, rv = line.partition("-")
                if dash == "-":
                    entry.update({lv.strip(): rv.strip()})
                else:
                    if entry:
                        yield entry
                        entry = {}
            if entry:
                yield entry


class MeSHReplaceReader:
    """Parser for MeSH replace file."""

    def __init__(self, filepath):
        """Constructor."""
        self.filepath = filepath

    def _parse_mh_line(self, line):
        """Parse MH line from replace.txt.

        :param line: str - MH line
        :return: dict - {"lv": ..., "rv": ...}
        """
        lv, eq, rv = line.partition("=")
        return {
            "lv": lv.strip(),
            "rv": rv.strip(),
        }

    def _parse_mh_old_line(self, line):
        """Parse MH OLD line.

        :param line: MH NEW line from replace.txt
        :return: dict - {
            "main_heading_old": ...,
            "delete": ...,
            "status": ...,
        }
        """
        mh_parsed = self._parse_mh_line(line)
        rv = mh_parsed["rv"]
        # Actually search for end part of rv that we DON'T want.
        # It has to be there for well-formed entries.
        m = re.search(r"(#?) \[(\w\*?)?\]$", rv)
        if not m:
            warnings.warn(f"Malformed line: {line}")
            return {}
        return {
            "main_heading_old": rv[:m.start()].strip(),
            "delete": m.group(1) or "",
            "status": m.group(2) or "",
        }

    def _parse_mh_new_line(self, line):
        """Parse MH NEW line.

        :param line: str - MH NEW line from replace.txt
        :return: dict - {main_heading_new: ...}
        """
        mh_parsed = self._parse_mh_line(line)
        rv = mh_parsed["rv"]
        return {
            "main_heading_new": rv,
        }

    def iter_internal_entries(self):
        """Read 'replace' file.

        This is a very simple parser that takes advantage of the
        structure of 'replace' files.

        Problems we've encountered in the source files, that we account for:
        - Malformed MH OLD line
        - Missing MH NEW line

        Design:
        - lazy load file to reduce memory footprint during read
        Output:
            yield
            {
                "main_heading_old": "...",
                "main_heading_new": "...",
                "delete": "...",
                "status": "...",
            }
        """
        MH_OLD_START = "MH OLD ="
        MH_NEW_START = "MH NEW ="
        with open(self.filepath, 'r') as f:
            entry = {}
            expect_mh = "old"
            for line in f:
                line = line.strip()

                if expect_mh == "old":
                    if line.startswith(MH_OLD_START):
                        piece = self._parse_mh_old_line(line)
                        if piece:
                            entry.update(piece)
                            expect_mh = "new"
                    else:
                        pass
                # assumed elif expect_mh == "new":
                else:
                    if line.startswith(MH_NEW_START):
                        piece = self._parse_mh_new_line(line)
                        # can't be empty so no need to check
                        entry.update(piece)
                        yield entry
                        expect_mh = "old"
                        entry = {}
                    else:
                        pass


class MeSHXMLReader:
    """MeSH XML Reader.

    Used to iteratively return internal entries from raw source.
    """

    def __init__(self, filepath, filter=lambda r: True):
        """Constructor."""
        self._filepath = filepath
        self._filter = filter

    def _raw_to_internal_entry(self, raw):
        """Convert raw entry to internal representation entry.

        :param raw: LXML etree.Element - descriptor record raw XML object
        """
        entry = {}
        entry["id"] = raw.findtext("DescriptorUI")
        entry["descriptor_class"] = raw.get("DescriptorClass")
        # returns None if none found
        entry["main_heading"] = raw.findtext("DescriptorName/String")
        entry["allowed_qualifiers"] = [
            {
                "id": aq.findtext("QualifierReferredTo/QualifierUI"),
                "main_heading": aq.findtext("QualifierReferredTo/QualifierName/String"),  # noqa
            }
            for aq in raw.iterfind("AllowableQualifiersList/AllowableQualifier")  # noqa
        ]

        return entry

    def iter_internal_entries(self):
        """Iteratively reads entries from file."""
        with open(self._filepath, "rb") as f:
            records_parsed = etree.iterparse(
                f,
                events=("end",),
                tag="DescriptorRecord",
                huge_tree=True
            )
            for _, element in records_parsed:
                entry = self._raw_to_internal_entry(element)

                if self._filter(entry):
                    yield entry

                # Free up memory so that iteration is low-memory-bound
                element.clear()
                while element.getprevious() is not None:
                    del element.getparent()[0]
