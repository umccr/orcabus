# Imports
from datetime import datetime
from os import environ
from pathlib import Path
from textwrap import dedent
from typing import Optional, List, Union
import pandas as pd
import snakemd
from datetime import timezone
from snakemd import Document
from tempfile import NamedTemporaryFile
from pandera.typing import DataFrame

from .dataframe_makers import (
    get_library_df, get_metadata_summary_df,
    get_files_df, get_fastq_df,
    get_analyses_df, get_fastq_summary_df
)
from .dataframe_summary_makers import (
    get_analyses_summary_df, get_secondary_files_summary_df
)
from .globals import SECTION_LEVEL, TABLE_COUNT
from .models import FastqSummaryModel, SecondaryFileSummaryModel, AnalysisSummaryModel, MetadataSummaryModel


def convert_underscored_list(string: str) -> str:
    return string.replace("__", " | ")


def write_rmarkdown_top_level_header(
        doc: Document
):
    """
    We have a specific syntax needed to write the document header, this includes the rlibrary setup.

    We don't
    :return:
    """
    doc.add_raw(dedent(
        """
        ---
        title: "__PACKAGING_SUMMARY_TITLE__"
        toctitle: "Contents"
        output: 
          html_document:
            toc: true
            toc_depth: 3
            toc_float: true
        date: "__PACKAGING_DATE__"
        ---

        ```{r setup, include=FALSE}
        knitr::opts_chunk$set(echo = FALSE, warning = FALSE)

        # Library imports
        suppressMessages(library(tidyverse))
        library(DT)
        ```

        """
    ).replace(
        "__PACKAGING_SUMMARY_TITLE__", environ['PACKAGE_NAME']
    ).replace(
        "__PACKAGING_DATE__", datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ))


def write_rmarkdown_header(
        doc: Document,
        section_level: int,
        title: str,
        add_tabset: bool = False
):
    """
    Write the header for the RMarkdown document.
    :param doc:
    :param section_level:
    :param title:
    :param add_tabset:
    :return:
    """
    doc.add_heading(
        title + (" {.tabset .tabset-fade .tabset-pills}" if add_tabset else ""),
        level=section_level
    )
    doc.add_raw("\n")


def write_rmarkdown_table(
        doc: Document,
        dataframe: pd.DataFrame,
        caption: str,
        hidden_columns: Optional[List[str]] = None,
        js_chunk: Optional[str] = None
):
    global TABLE_COUNT

    # We're adding another table, up the count!
    TABLE_COUNT += 1

    # Generate a temp file
    temp_file = Path(NamedTemporaryFile(delete=False, suffix=".csv").name)

    # Write the dataframe to the temp file
    dataframe.to_csv(temp_file, index=False, header=True)

    # Get hidden column indexes in the dataframe
    if hidden_columns is not None:
        hidden_columns_num = list(filter(
            lambda col_iter_: col_iter_ is not None,
            list(map(
                # Get location of the column then add 1 since we're using 1 based indexing
                # In R programming
                lambda column_iter_: (
                    (dataframe.columns.get_loc(column_iter_) + 1)
                    if column_iter_ in dataframe.columns.tolist() else None
                ),
                hidden_columns
            ))
        ))
    else:
        hidden_columns_num = []

    doc.add_raw(dedent(
        """
        ```{{r {__chunk_title__}}}
        readr::read_csv(
            '{__file_path__}',
            show_col_types = FALSE
        ) %>%
        DT::datatable(
            extensions=c('Buttons', 'KeyTable'),
            #filter='top',
            caption=htmltools::tags$caption(
                style = 'caption-side: bottom; text-align: center;',
                "{__caption_title__}", htmltools::em("{__caption__}")
            ),
            options=list(
                dom='Blfrtip',
                pageLength=5,
                scrollX=TRUE,
                keys=TRUE,
                lengthMenu = c(5, 10, 15, 20),
                columnDefs = list(
                    list(
                        visible = FALSE, 
                        searchable = TRUE, 
                        targets = c({__hidden_column_targets__})
                    )
                ),
                buttons=c('copy', 'csv', 'excel', 'pdf', 'print', 'colvis'),
                rowCallback = {__row_call_back__}
            )
        )
        ```
        """.format(
            **{
                "__chunk_title__": f"table_{TABLE_COUNT}",
                "__file_path__": str(temp_file),
                "__caption_title__": f"Table {TABLE_COUNT}:",
                "__caption__": caption,
                "__hidden_column_targets__": ", ".join(map(str, hidden_columns_num)),
                "__row_call_back__": f"JS(\"{js_chunk}\")" if js_chunk is not None else "NULL"
            }
        )
    ))


def add_summary_section(
        doc: Document,
        summary_df: Union[DataFrame[FastqSummaryModel], DataFrame[MetadataSummaryModel]],
        section_name: str = "summary",  # One of "Metadata" or "Fastq"
        hidden_columns: Optional[List[str]] = None
):
    """
    Add in the summary section to the document.
    :param hidden_columns:
    :param section_name:
    :param doc:
    :param summary_df:
    :return:
    """
    if summary_df is None:
        return

    # Add in our javascript chunk if 'Storage Class' is in the dataframe
    # Storage class is a hidden column, however we can use it to show if a file is in archive
    js_chunk = None
    if 'Storage Class' in summary_df.columns.tolist():
        # We need to add a javascript chunk to the table to show if the file is in archive
        # But we also use R 1-based indexing despite the fact were writing JS... in python... anyway
        # To add complications here the data attribute is prior to column removal, but the js update
        # is with column removal. We assume that the filename is the first column and the one we want to make red
        js_chunk = """
            function(row, data) {{
              if (data[{__storage_class_column_index__}] == 'DEEP_ARCHIVE') {{
                $(row).css('color', 'red');
              }}
            }}
        """.format(
            **{
                "__storage_class_column_index__": summary_df.columns.get_loc('Storage Class') + 1
            }
        )

    # We split by Project ID if there are multiple projects in the dataframe
    has_multiple_projects = (
        True if len(summary_df['Project ID'].unique()) > 1
        else False
    )

    # We also split by assay / type if there are multiple
    has_multiple_assay_type_combinations = (
        True if summary_df[['Assay', 'Type']].drop_duplicates().shape[0] > 1
        else False
    )

    # Add the section header
    # Simplest case, one project, one assay / type
    if not has_multiple_projects and not has_multiple_assay_type_combinations:
        write_rmarkdown_header(
            doc,
            section_level=SECTION_LEVEL,
            title=section_name.title(),
            add_tabset=False
        )
        write_rmarkdown_table(
            doc,
            dataframe=summary_df,
            caption=f"All {section_name} in the data package",
            hidden_columns=hidden_columns,
            js_chunk=js_chunk,
        )
        return

    # Either multiple projects or multiple assay / type combinations
    # First thing to do regardless is to write the metadata for 'all'
    write_rmarkdown_header(
        doc,
        section_level=SECTION_LEVEL,
        title=section_name.title(),
        add_tabset=True
    )
    # Write the metadata for 'all'
    write_rmarkdown_header(
        doc,
        section_level=SECTION_LEVEL + 1,
        title="All",
        add_tabset=False
    )
    write_rmarkdown_table(
        doc,
        dataframe=summary_df,
        caption=f"All {section_name} in the data package",
        hidden_columns=hidden_columns,
        js_chunk=js_chunk,
    )

    if not has_multiple_projects:
        # Generate the metadata for each assay / type combination
        # Iterate over the assay / type combinations
        for (assay, type_), assay_type_df in summary_df.groupby(['Assay', 'Type']):
            # Write the metadata for 'all'
            write_rmarkdown_header(
                doc,
                section_level=SECTION_LEVEL + 1,
                title=f"Assay '{convert_underscored_list(assay)}' / Type '{convert_underscored_list(type_)}'",
                add_tabset=False
            )
            write_rmarkdown_table(
                doc,
                dataframe=assay_type_df,
                caption=f"{section_name} for libraries with assay: '{convert_underscored_list(assay)}' and type: '{convert_underscored_list(assay)}'",
                hidden_columns=hidden_columns,
                js_chunk=js_chunk,
            )
        return

    # We have multiple projects in the metadata we may split further by assay / type for each project
    # But regardless the first thing we will do is split by project
    # Iterate over the projects
    for project_id, project_df in summary_df.groupby('Project ID'):
        has_multiple_assay_combinations = (
            False if project_df[['Assay', 'Type']].drop_duplicates().shape[0] == 1 else True
        )

        # Write the metadata for 'all'
        write_rmarkdown_header(
            doc,
            section_level=SECTION_LEVEL + 1,
            title=f"Project ID: {project_id}",
            add_tabset=has_multiple_assay_combinations
        )

        # If there is only one assay / type combination for this project, we do not need to split further
        if not has_multiple_assay_combinations:
            write_rmarkdown_table(
                doc,
                dataframe=project_df,
                caption=f"{section_name.title()} for libraries in project: '{project_id}'",
                hidden_columns=hidden_columns,
                js_chunk=js_chunk,
            )
            continue

        # Write the metadata for 'all'
        write_rmarkdown_header(
            doc,
            section_level=SECTION_LEVEL + 2,
            title=f"All",
            add_tabset=True
        )
        write_rmarkdown_table(
            doc,
            dataframe=project_df,
            caption=f"{section_name} for libraries in project: '{project_id}'",
            hidden_columns=hidden_columns,
            js_chunk=js_chunk,
        )

        # We have multiple assay / type combinations for this project (and multiple projects)
        # Certainly in the weeds here
        for (assay, type_), assay_type_df in project_df.groupby(['Assay', 'Type']):
            # Write the metadata for 'all'
            write_rmarkdown_header(
                doc,
                section_level=SECTION_LEVEL + 2,
                title=f"Assay: {assay} / Type: {type_}",
                add_tabset=False
            )
            write_rmarkdown_table(
                doc,
                dataframe=assay_type_df,
                caption=f"{section_name.title()} for libraries with assay: '{assay}' and type: '{type_}' in project: '{project_id}'",
                hidden_columns=hidden_columns,
                js_chunk=js_chunk,
            )

def add_metadata_section(
        doc: Document,
        metadata_df: DataFrame[MetadataSummaryModel],
):
    """
    Add the metadata section
    :param doc:
    :param metadata_df:
    :return:
    """
    add_summary_section(
        doc=doc,
        summary_df=metadata_df,
        section_name="metadata",
    )


def add_fastqs_section(
        doc: Document,
        fastq_df: DataFrame[FastqSummaryModel],
):
    """
    Like the metadata section, we split the fastqs section by project and assay / type.
    :param doc:
    :param fastq_df:
    :return:
    """
    """
    Add in the metadata section to the document.
    :param doc:
    :param fastq_df:
    :return:
    """
    hidden_fastq_columns = [
        "Sample ID",
        "External Sample ID",
        "Subject ID",
        "Individual ID",
        "Project ID",
        "Assay",
        "Type",
        "Storage Class"
    ]

    add_summary_section(
        doc=doc,
        summary_df=fastq_df,
        section_name="fastq",
        hidden_columns=hidden_fastq_columns
    )


def add_secondary_file_summary_section(
        doc: Document,
        summary_df: Union[DataFrame[AnalysisSummaryModel], DataFrame[SecondaryFileSummaryModel]],
        section_name: str = "summary",  # One of "secondary analyses" or "secondary files"
):
    """
    Add in the secondary file summary section to the document.

    Like the metadata or fastq summary sections, we split the secondary file summary section by project and assay / type.
    However we also split by portal run id if applicable
    :param doc:
    :param summary_df:
    :return:
    """
    if summary_df is None:
        return

    hidden_analyses_columns = [
        "Library ID",
        "Sample ID",
        "External Sample ID",
        "Subject ID",
        "Individual ID",
        "Project ID",
        "Assay",
        "Type",
        "Storage Class"
    ]

    # Add in our javascript chunk if 'Storage Class' is in the dataframe
    # Storage class is a hidden column, however we can use it to show if a file is in archive
    js_chunk = None
    if 'Storage Class' in summary_df.columns.tolist():
        # We need to add a javascript chunk to the table to show if the file is in archive
        # But we also use R 1-based indexing despite the fact were writing JS... in python... anyway
        # To add complications here the data attribute is prior to column removal, but the js update
        # is with column removal. We assume that the filename is the first column and the one we want to make red
        js_chunk = """
            function(row, data) {{
              if (data[{__storage_class_column_index__}] == 'DEEP_ARCHIVE') {{
                $(row).css('color', 'red');
              }}
              if (data[{__storage_class_column_index__}] == 'GLACIER') {{
                $(row).css('color', 'red');
              }}
              if (data[{__storage_class_column_index__}] == 'GLACIER_INSTANT_RETRIEVAL') {{
                $(row).css('color', 'purple');
              }}
            }}
        """.format(
            **{
                "__storage_class_column_index__": summary_df.columns.get_loc('Storage Class') + 1
            }
        )

    # We split by Project ID if there are multiple projects in the dataframe
    has_multiple_projects = (
        True if len(summary_df['Project ID'].unique()) > 1
        else False
    )

    # We also split by assay / type if there are multiple
    has_multiple_assay_type_combinations = (
        True if summary_df[['Assay', 'Type']].drop_duplicates().shape[0] > 1
        else False
    )

    # Add the metadata section header
    # Simplest case, one project, one assay / type
    if not has_multiple_projects and not has_multiple_assay_type_combinations:
        write_rmarkdown_header(
            doc,
            section_level=SECTION_LEVEL,
            title=section_name.title(),
            add_tabset=False
        )
        write_rmarkdown_table(
            doc,
            dataframe=summary_df,
            caption=f"All {section_name} in the data package",
            hidden_columns=hidden_analyses_columns,
            js_chunk=js_chunk,
        )
        return

    # Either multiple projects or multiple assay / type combinations
    # First thing to do regardless is to write the metadata for 'all'
    write_rmarkdown_header(
        doc,
        section_level=SECTION_LEVEL,
        title=section_name.title(),
        # We only add a tabset if we don't have multiple projects or assay / type combinations
        # And instead split by project id first and then split by assay / type
        add_tabset=(not ( has_multiple_projects and has_multiple_assay_type_combinations))
    )
    # Write the metadata for 'all'
    write_rmarkdown_header(
        doc,
        section_level=SECTION_LEVEL + 1,
        title="All",
        add_tabset=False
    )
    write_rmarkdown_table(
        doc,
        dataframe=summary_df,
        caption=f"All {section_name} data in the data package",
        hidden_columns=hidden_analyses_columns,
        js_chunk=js_chunk,
    )

    if not has_multiple_projects:
        # Generate the metadata for each assay / type combination
        # Iterate over the assay / type combinations
        for (assay, type_), assay_type_df in summary_df.groupby(['Assay', 'Type']):
            # Write the metadata for 'all'
            write_rmarkdown_header(
                doc,
                section_level=SECTION_LEVEL + 1,
                title=f"Assay '{assay}' / Type '{type_}'",
                add_tabset=False
            )
            write_rmarkdown_table(
                doc,
                dataframe=assay_type_df,
                caption=f"Secondary analysis data for libraries with assay: '{assay}' and type: '{type_}'",
                hidden_columns=hidden_analyses_columns,
                js_chunk=js_chunk,
            )
        return

    # We have multiple projects in the metadata we may split further by assay / type for each project
    # But regardless the first thing we will do is split by project
    # Iterate over the projects
    for project_id, project_df in summary_df.groupby('Project ID'):
        has_multiple_assay_combinations = (
            False if project_df[['Assay', 'Type']].drop_duplicates().shape[0] == 1 else True
        )

        # Write the metadata for 'all'
        write_rmarkdown_header(
            doc,
            section_level=SECTION_LEVEL + 1,
            title=f"Project ID: {project_id}",
            add_tabset=has_multiple_assay_combinations
        )

        # If there is only one assay / type combination for this project, we do not need to split further
        if not has_multiple_assay_combinations:
            write_rmarkdown_table(
                doc,
                dataframe=project_df,
                caption=f"{section_name.title()} for libraries in project: '{project_id}'",
                hidden_columns=hidden_analyses_columns,
                js_chunk=js_chunk,
            )
            continue

        # Write the metadata for 'all'
        write_rmarkdown_header(
            doc,
            section_level=SECTION_LEVEL + 2,
            title=f"All",
            add_tabset=False
        )
        write_rmarkdown_table(
            doc,
            dataframe=project_df,
            caption=f"{section_name} for libraries in project: '{project_id}'",
            hidden_columns=hidden_analyses_columns,
            js_chunk=js_chunk,
        )

        # We have multiple assay / type combinations for this project (and multiple projects)
        # Certainly in the weeds here
        for (assay, type_), assay_type_df in project_df.groupby(['Assay', 'Type']):
            # Write the metadata for 'all'
            write_rmarkdown_header(
                doc,
                section_level=SECTION_LEVEL + 2,
                title=f"Assay: {assay} / Type: {type_}",
                add_tabset=False
            )
            write_rmarkdown_table(
                doc,
                dataframe=assay_type_df,
                caption=f"{section_name.title()} for libraries with assay: '{assay}' and type: '{type_}' in project: '{project_id}'",
                hidden_columns=hidden_analyses_columns,
                js_chunk=js_chunk,
            )


def add_analyses_section(
        doc: Document,
        analyses_summary_df: Optional[DataFrame[AnalysisSummaryModel]],
):
    add_secondary_file_summary_section(
        doc=doc,
        summary_df=analyses_summary_df,
        section_name="secondary analyses",
    )


def add_secondary_files_section(
        doc: Document,
        secondary_files_df: DataFrame[SecondaryFileSummaryModel],
):
    """
    Similar to the analyses section, we split the secondary files section by project and type.
    The purpose of these tables is for users to be able to see the output location for certain files in the analyses.
    We provide the following information for secondary files:
    * File Name
    * Workflow Name
    * Portal Run ID
    * Output Path
    """
    add_secondary_file_summary_section(
        doc=doc,
        summary_df=secondary_files_df,
        section_name="secondary files",
    )



def generate_data_summary_report_template(job_id: str) -> None:
    """
    Generate the RMarkdown template for the data summary report.
    :return:
    """
    # Get the library df
    library_df = get_library_df(job_id)

    # Get the metadata
    metadata_summary_df = get_metadata_summary_df(
        library_df=library_df
    )

    # Initialise snake doc
    doc = snakemd.new_doc()
    write_rmarkdown_top_level_header(doc)

    # Add metadata section to document
    add_metadata_section(doc, metadata_summary_df)

    # Get the files df
    files_df = get_files_df(
        job_id=job_id
    )

    # Get the fastqs
    fastq_df = get_fastq_df(
        job_id=job_id,
        library_df=library_df,
        files_df=files_df,
    )

    if fastq_df is not None:
        # Get the fastq df as a summary
        fastq_summary_df = get_fastq_summary_df(
            fastq_df=fastq_df,
        )

        # Add fastqs section to document
        add_fastqs_section(doc, fastq_summary_df)

    # Get the analyses
    analyses_df = get_analyses_df(
        job_id=job_id,
        library_df=library_df,
        files_df=files_df
    )

    if analyses_df is not None:
        analyses_summary_df = get_analyses_summary_df(
            analyses_df=analyses_df
        )

        # Get the secondary files
        secondary_files_summary_df = get_secondary_files_summary_df(
            analyses_df=analyses_df
        )

        # Add analyses section to document
        add_analyses_section(doc, analyses_summary_df)

        # Add secondary files section to document
        add_secondary_files_section(doc, secondary_files_summary_df)


    # Write the document to a file
    doc.dump("data_summary_report", ext="Rmd")
