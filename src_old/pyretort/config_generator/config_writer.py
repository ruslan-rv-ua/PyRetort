from enum import StrEnum
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from pyretort.constants import CONFIG_FILE_NAME


class ConfigTemplates(StrEnum):
    SHORT = "short_config.toml.j2"
    DETAILED = "detailed_config.toml.j2"


def write_config(
    *,
    output_dir: Path,
    context: dict,
    template_name: ConfigTemplates = ConfigTemplates.SHORT,
) -> None:
    env = Environment(
        loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
        auto_reload=True,
    )
    template = env.get_template(str(template_name))
    rendered_content = template.render(context)
    output_file = output_dir / CONFIG_FILE_NAME
    output_file.write_text(rendered_content, encoding="utf-8")
