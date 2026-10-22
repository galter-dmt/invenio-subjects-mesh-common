# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-2026 Northwestern University.
#
# invenio-subjects-mesh-common is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""MeSH Command line tool."""

from datetime import date
from pathlib import Path

import click
from flask.cli import with_appcontext
from galter_subjects_utils.adapter import converted_to_subjects
from galter_subjects_utils.deltor import DeltasGenerator
from galter_subjects_utils.keeptrace import KeepTrace
from galter_subjects_utils.reader import get_rdm_subjects
from galter_subjects_utils.writer import write_csv

from .converter import MeSHRDMConverter, MeSHRDMReplaceConverter
from .downloader import MeSHDownloader, RequestsDownloader
from .reader import MeSHReplaceReader, MeSHXMLReader, topic_filter
from .scheme import MeSHScheme

defaults = {
    "year": date.today().year,
    "filter": "topic-qualifier",
    "downloads-dir": Path.cwd(),
    "output-file": Path.cwd(),
}


def to_mesh_downloader_kwargs(parameters):
    """To MeSHDownloader kwargs."""
    result = {
        "year": parameters["year"],
        "cache": not parameters["no_cache"],
        "directory": Path.cwd() / parameters["downloads_dir"]
    }

    return result


# Options


option_for_downloads_dir = click.option(
    "--downloads-dir", "-d",
    type=click.Path(path_type=Path),
    default=defaults["downloads-dir"]
)
option_for_year = click.option("--year", "-y", default=defaults["year"])
option_for_filter = click.option(
    "--filter",
    "-f",
    type=click.Choice(["topic", "topic-qualifier"]),
    default=defaults["filter"],
)


# Commands


@click.group()
def mesh():
    """MeSH related commands."""


@mesh.command("download")
@option_for_downloads_dir
@click.option(
    "--no-cache",
    default=False,
    help="Re-download even if already downloaded.",
    is_flag=True
)
@option_for_year
def mesh_download(**parameters):
    """Download MeSH files."""
    downloader_kwargs = to_mesh_downloader_kwargs(parameters)
    downloader = MeSHDownloader(
        **downloader_kwargs,
        download_engine=RequestsDownloader(),
    )
    downloader.download()

    print(f"Raw MeSH files written in {parameters['downloads_dir']}/")


@mesh.command("file")
@option_for_downloads_dir
@option_for_filter
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    default=defaults["output-file"] / "subjects_mesh.jsonl",
)
@option_for_year
def mesh_file(**parameters):
    """Generate new MeSH subjects file."""
    # 'Empty' downloader just to pass it to reader, so that it can retrieve
    # relevant filepaths.
    downloader = MeSHDownloader(
        directory=parameters["downloads_dir"],
        year=parameters["year"],
    )

    # Read
    reader = MeSHXMLReader(
        downloader.terms_filepath,
        filter=topic_filter,
    )

    # Convert
    converter = MeSHRDMConverter(reader.iter_internal_entries())

    # Write
    header = ["id", "scheme", "subject"]
    filepath = write_csv(
        converter.iter_rdm_subjects(
            qualified=(parameters["filter"] == "topic-qualifier")
        ),
        parameters["output_file"],
        writer_kwargs={"fieldnames": header},
    )

    print(f"MeSH terms written here {filepath}")


@mesh.command("deltas")
@option_for_downloads_dir
@option_for_year
@option_for_filter
@click.option(
    "--output-file", "-o",
    type=click.Path(path_type=Path),
    default=defaults["output-file"] / "deltas.csv",
)
@with_appcontext
def mesh_deltas(**parameters):
    """Write MeSH subject delta operations to file."""
    print("Generating deltas...")
    downloads_dir = parameters["downloads_dir"].expanduser()
    year = parameters["year"]
    filter_ = parameters["filter"]
    mesh = MeSHScheme()

    # Source subjects
    subject_rdm_preexisting = get_rdm_subjects(scheme=mesh.name)
    src = converted_to_subjects(subject_rdm_preexisting, mesh.prefix)

    # Destination subjects
    subjects_fp = downloads_dir / f"desc{year}.xml"
    reader_dst = MeSHXMLReader(subjects_fp, filter=topic_filter)
    entries = reader_dst.iter_internal_entries()
    converted = MeSHRDMConverter(entries).iter_rdm_subjects(
        qualified=(filter_ == "topic-qualifier")
    )
    dst = converted_to_subjects(converted, mesh.prefix)

    # Replacements
    replace_fp = downloads_dir / f"replace{year}.txt"
    replacements_internal = (
        MeSHReplaceReader(replace_fp).iter_internal_entries()
    )
    replacements_rdm = MeSHRDMReplaceConverter(replacements_internal).convert()

    ops = (
        DeltasGenerator(
            src_subjects=src,
            dst_subjects=dst,
            scheme=mesh,
            replacements=replacements_rdm
        )
        .generate()
    )
    # in-place
    KeepTrace.mark(
        ops,
        # only can keep trace of *those* anyway
        yes_logic=lambda op: op["type"] in ["rename", "replace", "remove"]
    )

    deltas_fp = parameters["output_file"]
    header = [
        "id",
        "type",
        "scheme",
        "subject",
        "new_id",
        "new_subject",
        "keep_trace"
    ]
    write_csv(
        ops,
        deltas_fp,
        writer_kwargs={
            "fieldnames": header
        }
    )

    print(f"MeSH deltas written here {deltas_fp}")
