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
from galter_subjects_utils.deltas_generators import DeltasGenerator
from galter_subjects_utils.reader import get_rdm_subjects, read_csv
from galter_subjects_utils.serdes import DeltaSerdes, SubjectRDMSerdes
from galter_subjects_utils.writer import write_csv

from .converters import (
    MeSHRDMConverter,
    MeSHToDeltasGeneratorReplacementsConverter,
)
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
@click.option(
    "--subjects-file",
    "-s",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    required=True,
)
@click.option(
    "--replacements-file",
    "-r",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    default=defaults["output-file"] / "deltas.csv",
)
@with_appcontext
def mesh_deltas(**parameters):
    """Write MeSH subject delta operations to file."""
    print("Generating deltas...")

    mesh = MeSHScheme()
    subject_rdm_serdes = SubjectRDMSerdes()

    # Source subjects
    subjects_rdm_src = get_rdm_subjects(scheme=mesh.name)
    src = (
        subject_rdm_serdes.deserialize(s) for s in subjects_rdm_src
    )

    # Destination subjects
    subjects_rdm_dst = read_csv(parameters["subjects_file"])
    dst = (
        subject_rdm_serdes.deserialize(s) for s in subjects_rdm_dst
    )

    # Replacements
    replacements_internal = (
        MeSHReplaceReader(parameters["replacements_file"])
        .iter_internal_entries()
    )
    # Get iterables of Subjects used by replacement converter to provide the
    # Subjects corresponding to the labels read from the replacement file.
    # MeSH's replacement file maps old label to new label without providing id
    # (!). Those are the same as the src and dst above but need to be
    # duplicated because iterating over an iterable spends it.
    # **Subjects data source for old labels**
    # Potential TODO: filtering could be done at DB level to only get ones of
    # interest
    subjects_rdm_src = get_rdm_subjects(scheme=mesh.name)
    subjects_pool_src = (
        subject_rdm_serdes.deserialize(s) for s in subjects_rdm_src
    )
    # **Subjects data source for new labels**
    subjects_rdm_dst = read_csv(parameters["subjects_file"])
    subjects_pool_dst = (
        subject_rdm_serdes.deserialize(s) for s in subjects_rdm_dst
    )
    # **Replacements used by DeltasGenerator**
    replacement_converter = MeSHToDeltasGeneratorReplacementsConverter(
        replacements_internal,
        subjects_pool_src=subjects_pool_src,
        subjects_pool_dst=subjects_pool_dst,
    )
    replacements = replacement_converter.convert()

    # Deltas
    deltas_generator = DeltasGenerator(
        src_subjects=src,
        dst_subjects=dst,
        replacements=replacements,
    )
    deltas = deltas_generator.iter_deltas()

    delta_serdes = DeltaSerdes()
    deltas_serialized = (delta_serdes.serialize(d) for d in deltas)
    deltas_fp = parameters["output_file"]
    header = [
        "type",
        "id_src",
        "scheme_src",
        "subject_src",
        "id_dst",
        "scheme_dst",
        "subject_dst",
        "keep_trace",
    ]
    write_csv(
        deltas_serialized,
        deltas_fp,
        writer_kwargs={
            "fieldnames": header
        }
    )

    print(f"MeSH deltas written here {deltas_fp}")
