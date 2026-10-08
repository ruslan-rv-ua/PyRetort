"""Write Windows launchers from the compiled templates and add icons to them.

Functions:
- launcher_template: The template for a Python architecture and the console flag.
- generate_exe: Write a launcher that runs a command string, with an optional icon.
- add_icon_to_exe: Add an icon file to an existing executable file.

The templates are built from launcher/launcher.c by launcher/build.py. Each
holds the marker COMMAND_PLACEHOLDER followed by zeros, COMMAND_CAPACITY UTF-16
units in all; generate_exe overwrites that region with the command.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Any, BinaryIO

import win32api

from pyretort.types import PythonArchitecture

##### generate exe

TEMPLATES_DIR = Path(__file__).parent.absolute().resolve() / "templates"
MAX_CMD_LENGTH = 1023
COMMAND_CAPACITY = MAX_CMD_LENGTH + 1
COMMAND_PLACEHOLDER = "PYRETORT-LAUNCHER-COMMAND-PLACEHOLDER"


def launcher_template(architecture: PythonArchitecture, show_console: bool) -> Path:
    """Return the launcher template for a Python architecture and the console flag.

    Args:
        architecture: The architecture of the embedded Python the launcher starts.
        show_console: True for the console variant, False for the GUI variant.
    """
    variant = "console" if show_console else "gui"
    return TEMPLATES_DIR / f"launcher-{architecture.value}-{variant}"


def generate_exe(
    target: Path,
    command: str,
    icon_file: Path | None = None,
    show_console: bool = True,
    architecture: PythonArchitecture = PythonArchitecture.AMD64,
) -> None:
    """Write a launcher that runs a command string, with an optional icon.

    Args:
        target (Path): The path to the target executable file.
        command (str): The command line the launcher starts; every {EXE_DIR}
            in it is replaced with the launcher's directory at run time, and
            the launcher's own arguments are appended verbatim.
        icon_file (Optional[Path], optional): The path to the icon file to be added
            to the executable. Defaults to None.
        show_console (bool, optional): Whether to show the console window
            when the executable is run. Defaults to True.
        architecture (PythonArchitecture, optional): The architecture of the
            launcher, the same as the embedded Python's. Defaults to AMD64.

    Raises:
        ValueError: If the command is longer than MAX_CMD_LENGTH UTF-16 units;
            the template has room for exactly that many.
        RuntimeError: If the template does not hold the placeholder exactly once.
    """
    target = target.absolute().resolve()
    encoded_command = command.encode("utf-16-le")
    length = len(encoded_command) // 2
    if length > MAX_CMD_LENGTH:
        raise ValueError(
            f"Launcher command is {length} characters long; "
            f"the limit is {MAX_CMD_LENGTH}: {command}"
        )
    template = launcher_template(architecture, show_console)
    data = template.read_bytes()
    marker = COMMAND_PLACEHOLDER.encode("utf-16-le")
    if data.count(marker) != 1:
        raise RuntimeError(
            f"Launcher template {template} must contain the command placeholder "
            f"exactly once, found {data.count(marker)} occurrences"
        )
    start = data.index(marker)
    region_size = COMMAND_CAPACITY * 2
    region = encoded_command.ljust(region_size, b"\0")
    target.write_bytes(data[:start] + region + data[start + region_size :])
    if icon_file is not None:
        icon_file = Path(icon_file).absolute().resolve()
        add_icon_to_exe(target_exe_file=target, source_icon_file=icon_file)


###############################################################################
# add icon to exe
###############################################################################

# Documentation on struct specifications and their use can be found here:
# https://web.archive.org/web/20160531004250/https://msdn.microsoft.com/en-us/library/ms997538.aspx
ICONDIRHEADER = (("idReserved", "idType", "idCount"), "hhh")
ICONDIRENTRY = (
    (
        "bWidth",
        "bHeight",
        "bColorCount",
        "bReserved",
        "wPlanes",
        "wBitCount",
        "dwBytesInRes",
        "dwImageOffset",
    ),
    "bbbbhhii",
)
GRPICONDIRENTRY = (
    (
        "bWidth",
        "bHeight",
        "bColorCount",
        "bReserved",
        "wPlanes",
        "wBitCount",
        "dwBytesInRes",
        "nID",
    ),
    "bbbbhhih",
)
RT_ICON = 3
RT_GROUP_ICON = 14


class DataStruct:
    """General class for handling data structures within a file."""

    def __init__(
        self,
        dtype: tuple[tuple[str, ...], str],
        input_stream: BinaryIO | None = None,
    ) -> None:
        """Initialize a new instance of the DataStruct class.

        Args:
            dtype: A tuple of the form (field_names, data_types), where
                field_names is a tuple of strings representing the names of the fields
                in the data structure, and data_types is a string representing the
                data types of the fields in the data structure.
            input_stream: An optional input stream from which to read the data
                structure. If None, the data structure will be initialized to all
                zeros.

        Returns:
            - None.
        """
        self.__dict__["_field_names"] = dtype[0]
        self._data_types = dtype[1]
        assert len(self._field_names) == len(self._data_types)
        self._indices = {}
        for i, name in enumerate(self._field_names):
            self._indices[name] = i
        self._size = struct.calcsize(self._data_types)
        self._data = list(
            struct.unpack(
                self._data_types,
                bytearray(self._size)
                if input_stream is None
                else input_stream.read(self._size),
            )
        )

    def __getattr__(self, name: str) -> Any:
        """Retrieve the value of the specified attribute.

        Args:
            name: A string representing the name of the attribute to retrieve.

        Returns:
            The value of the specified attribute, if it exists.

        Raises:
            AttributeError: If the specified attribute does not exist.
        """
        if name in self._field_names:
            return self._data[self._indices[name]]
        return self.__dict__[name]

    def __setattr__(self, name: str, value: Any) -> None:
        """Set the value of the specified attribute.

        Args:
            name: A string representing the name of the attribute to set.
            value: The value to set the attribute to.

        Returns:
            None.

        Raises:
            AttributeError: If the specified attribute does not exist.
        """
        if name in self._field_names:
            self._data[self._indices[name]] = value
        else:
            self.__dict__[name] = value

    def _get_data(self) -> bytes:
        return struct.pack(self._data_types, *self._data)

    def _copy(self, data_struct: DataStruct) -> None:
        for field_name in data_struct._field_names:
            if field_name in self._field_names:
                setattr(self, field_name, getattr(data_struct, field_name))


class Icon:
    """Class to extract the relevant data from a .ico file."""

    def __init__(self, file_name: Path) -> None:
        """Initialize an Icon object by reading the specified icon file.

        Args:
            file_name: A Path object representing the path to the icon file.

        Returns:
            None.
        """
        with open(str(file_name), "rb") as f:
            self._header = DataStruct(dtype=ICONDIRHEADER, input_stream=f)
            self._dir_entries = [
                DataStruct(dtype=ICONDIRENTRY, input_stream=f)
                for _ in range(self._header.idCount)
            ]
            self._icon_data: list[bytes] = []
            for entry in self._dir_entries:
                f.seek(entry.dwImageOffset, 0)
                self._icon_data.append(f.read(entry.dwBytesInRes))

    def _get_header_and_group_icon_dir_data(self) -> bytes:
        data = self._header._get_data()
        for i, dir_entry in enumerate(self._dir_entries):
            icon_dir_entry = DataStruct(dtype=GRPICONDIRENTRY)
            icon_dir_entry._copy(data_struct=dir_entry)
            icon_dir_entry.nID = i + 1
            data += icon_dir_entry._get_data()
        return data

    def _get_icon_data(self) -> list[bytes]:
        return self._icon_data


def add_icon_to_exe(source_icon_file: Path, target_exe_file: Path) -> None:
    """Add an icon to a Windows executable file.

    Args:
        source_icon_file: A Path object representing the path to the icon file.
        target_exe_file: A Path object representing the path to the executable file.

    Returns:
        None.

    Raises:
        FileNotFoundError: If either the source icon file or the target executable file
            could not be found or is not a valid file.
    """
    target_exe_file = target_exe_file.absolute().resolve()
    if not target_exe_file.is_file():
        raise FileNotFoundError(
            "The target executable file could not be found or is not a valid file: "
            f"{target_exe_file}"
        )
    source_icon_file = source_icon_file.absolute().resolve()
    if not source_icon_file.is_file():
        raise FileNotFoundError(
            "The icon file could not be found or is not a valid file: "
            f"{source_icon_file}"
        )
    icon = Icon(file_name=source_icon_file)
    ur_handle = win32api.BeginUpdateResource(str(target_exe_file), 0)
    win32api.UpdateResource(
        ur_handle, RT_GROUP_ICON, 0, icon._get_header_and_group_icon_dir_data()
    )
    for i, icon_data in enumerate(icon._get_icon_data()):
        win32api.UpdateResource(ur_handle, RT_ICON, i + 1, icon_data)
    win32api.EndUpdateResource(ur_handle, 0)
