from pathlib import Path

import slugify

from ..constants import (
    BUILD_OUTPUT_DIR_DEFAULT,
    DIST_OUTPUT_DIR_DEFAULT,
    DOWNLOAD_CACHE_DIR_DEFAULT,
    PYDIST_DIR_DEFAULT,
    SHOW_CONSOLE_DEFAULT,
)
from .config_writer import ConfigTemplates, write_config
from .project_data import (
    find_icon_path,
    find_main_file,
    find_project_name,
    find_project_version,
    find_source_subdir,
)
from .python_info_finder import (
    get_current_python_architecture,
    get_current_python_version,
)
from .requirements_finder import find_requirements


def gether_project_data(project_root: Path) -> dict:
    project_name = find_project_name(project_root)
    requirements = find_requirements(project_root)
    project_source_subdir = find_source_subdir(project_root, project_name)
    project_source_path = project_root / project_source_subdir
    project_main_file = find_main_file(project_source_path, project_name)
    run_as_package = project_main_file == "__main__.py"
    python_version = get_current_python_version()
    python_architecture = get_current_python_architecture()

    slugified_project_name = slugify.slugify(
        project_name, lowercase=True, separator="-"
    )
    exe_file_name = f"{slugified_project_name}.exe"
    icon_path = find_icon_path(project_root)

    dist_zip_file_name_parts = [slugified_project_name]
    project_version = find_project_version(project_root)
    if project_version:
        dist_zip_file_name_parts.extend((project_version, python_architecture.value))
    dist_zip_file_name = "-".join(dist_zip_file_name_parts) + ".zip"

    data = {
        "project_name": project_name,
        "project_version": project_version,
        "project_dir": project_root,
        "requirements": requirements,
        "project_source_subdir": project_source_subdir,
        "main_file": project_main_file,
        "run_as_package": run_as_package,
        "python_version": python_version,
        "python_architecture": python_architecture,
        "pydist_dir": PYDIST_DIR_DEFAULT,
        "build_source_dir": Path(slugify.slugify(project_name, separator="_")),
        "exe_file_name": exe_file_name,
        "icon_path": icon_path,
        "show_console": SHOW_CONSOLE_DEFAULT,
        "dist_zip_file_name": dist_zip_file_name,
        "download_cache_dir": DOWNLOAD_CACHE_DIR_DEFAULT,
        "build_output_dir": BUILD_OUTPUT_DIR_DEFAULT,
        "dist_output_dir": DIST_OUTPUT_DIR_DEFAULT,
    }
    return data


def generate_config_file(
    project_root: Path, project_data: dict, with_comments: bool = False
) -> None:
    template_name = ConfigTemplates.DETAILED if with_comments else ConfigTemplates.SHORT
    write_config(
        output_dir=project_root, context=project_data, template_name=template_name
    )


__all__ = [
    "gether_project_data",
    "generate_config_file",
]
