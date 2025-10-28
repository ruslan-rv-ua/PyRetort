import shutil
from fnmatch import fnmatch
from pathlib import Path

from pyretort.builder.exe_generator import generate_exe
from pyretort.constants import DEFAULT_BLACKLIST
from pyretort.types import BuildConfig


class BuildManager:
    def __init__(self, config: BuildConfig, clear_build_folder: bool = True) -> None:
        self._config = config
        if clear_build_folder:
            self._clear_build_directory()

    def build(self) -> None:
        # Placeholder for build logic
        pass

    def copy_python_interpreter(self, copy_from: Path) -> None:
        pydist_dir = self._config.pydist_dir_absolute
        shutil.copytree(copy_from, pydist_dir, dirs_exist_ok=True)

    def copy_source_files(self) -> None:
        """Copy source files to the build source directory, respecting inclusion/exclusion rules.

        If white_list is not empty, only files matching patterns in white_list are copied.
        Otherwise, all files are copied except those matching patterns in black_list.

        """
        source_dir = self._config.project_source_dir
        dest_dir = self._config.build_source_dir_absolute
        dest_dir.mkdir(parents=True, exist_ok=True)

        white_list = []
        if white_list:
            self._copy_with_whitelist(source_dir, dest_dir, white_list)
        black_list = DEFAULT_BLACKLIST.copy()
        black_list.append(str(self._config.download_cache_dir))
        black_list.append(str(self._config.build_output_dir))
        black_list.append(str(self._config.dist_output_dir))
        self._copy_with_blacklist(source_dir, dest_dir, black_list)

    def make_executable(self) -> None:
        """Generate the executable launcher file.

        Creates a Windows executable (.exe) that launches the Python application
        with the correct interpreter and command line arguments.
        """
        exe_path = self._config.build_output_dir_absolute / self._config.exe_file_name

        # Determine which Python executable to use based on console visibility
        python_exe_file_name = (
            "python.exe" if self._config.show_console else "pythonw.exe"
        )

        python_exe_path = self._config.pydist_dir_absolute / python_exe_file_name
        relative_python_exe_path = python_exe_path.relative_to(
            self._config.build_output_dir_absolute
        )
        print(f"Using python executable: {relative_python_exe_path}")

        if self._config.run_as_package:
            print("Building executable to run as package")
            relative_dir = self._config.build_source_dir_absolute.relative_to(
                self._config.build_output_dir_absolute
            )
            target = f"-m {relative_dir}"
        else:
            print("Building executable to run as script")
            if self._config.main_file is None:
                raise ValueError("main_file must be specified when running as script")
            main_file = self._config.build_source_dir_absolute / self._config.main_file
            relative_main_file = main_file.relative_to(
                self._config.build_output_dir_absolute
            )
            target = relative_main_file

        command = f"{relative_python_exe_path} {target}"
        print(f"Generated command for executable: {command}")
        generate_exe(
            target=exe_path,
            command=command,
            icon_file=self._config.icon_path_absolute,
            show_console=self._config.show_console,
        )

    def _build_python_command(self, python_exe: str) -> str:
        """Construct the Python command for running the application.

        Args:
            python_exe: Path to the Python executable (relative to build output)

        Returns:
            Complete command string to execute the Python application

        Raises:
            ValueError: If main_file is None when running as script
        """
        if self._config.run_as_package:
            # Run as package: python -m package_name
            package_name = self._prepare_package_name()
            return f"{python_exe} -m {package_name}"
        else:
            # Run as script: python source_dir/main_file.py
            if self._config.main_file is None:
                raise ValueError("main_file must be specified when running as script")
            main_file_path = str(self._config.build_source_dir / self._config.main_file)
            return f"{python_exe} {main_file_path}"

    def _clear_build_directory(self) -> None:
        build_dir = self._config.build_output_dir_absolute
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True, exist_ok=True)

    def _copy_with_whitelist(
        self, source_dir: Path, dest_dir: Path, white_list: list[str]
    ) -> None:
        """Copy only files matching whitelist patterns.

        White list patterns are matched against file paths relative to source_dir.
        Example patterns: 'src/*.py', 'data/**', 'README.md'.
        """
        files_to_copy = set()
        for pattern in white_list:
            files_to_copy.update(
                item for item in source_dir.rglob(pattern) if item.is_file()
            )

        for item in files_to_copy:
            relative_path = item.relative_to(source_dir)
            dest_path = dest_dir / relative_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest_path)

    def _copy_with_blacklist(
        self, source_dir: Path, dest_dir: Path, black_list: list[str]
    ) -> None:
        """Copy all files except those matching blacklist patterns.

        Black list patterns are matched against file paths relative to source_dir.
        Example patterns: 'build', '*.pyc', '__pycache__'.
        """
        for item in source_dir.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(source_dir)
                if self._should_exclude(relative_path, black_list):
                    continue
                dest_path = dest_dir / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)

    def _should_exclude(self, relative_path: Path, black_list: list[str]) -> bool:
        """Check if a file path matches any blacklist pattern."""
        parts = relative_path.parts

        for pattern in black_list:
            # 1. Check path component (e.g., 'build', '__pycache__')
            if pattern in parts:
                return True

            # 2. Check full relative path (e.g., 'src/logs/*.log')
            if relative_path.match(pattern):
                return True

            # 3. Check only file name (e.g., '*.pyc', '.DS_Store')
            # This fixes the error when '*.pyc' did not find 'src/main.pyc'
            if fnmatch(relative_path.name, pattern):
                return True

        return False
