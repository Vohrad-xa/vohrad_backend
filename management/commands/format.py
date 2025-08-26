"""Professional precision code formatter - elegant, efficient, and uncompromising."""

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))
import typer

app = typer.Typer(help="Precision code formatting - crafted for perfection")


@dataclass(frozen=True)
class FormattingConfig:
    """Immutable configuration for precision formatting."""
    
    max_line_length: int = 120
    aggressive_level: int = 2
    excluded_patterns: Set[str] = frozenset({
        "migrations", "__pycache__", ".git", ".venv", "venv", ".pytest_cache"
    })
    
    # Regex patterns for precision formatting
    IMPORT_SECTION = re.compile(r'((?:^(?:from\s+\S+\s+)?import\s+.+\n)+)(\n*)', re.MULTILINE)
    EXCESSIVE_BLANKS = re.compile(r'\n{3,}')
    CLASS_DEFINITION = re.compile(r'\n{3,}(class\s+\w+)')
    FUNCTION_DEFINITION = re.compile(r'\n{3,}(def\s+\w+)')


class PrecisionFormatter:
    """Elegant code formatter that transforms Python into art."""
    
    def __init__(self, config: FormattingConfig = FormattingConfig()):
        self.config = config
        self._stats = {"files_processed": 0, "files_modified": 0, "errors": 0}
    
    def format_content(self, content: str) -> Tuple[str, bool]:
        """Transform content with precision formatting rules."""
        original = content
        
        # Pipeline of transformations - order matters
        content = self._normalize_line_endings(content)
        content = self._format_import_section(content)
        content = self._apply_class_spacing(content)
        content = self._remove_excessive_blanks(content)
        content = self._format_method_spacing(content)
        content = self._finalize_formatting(content)
        
        return content, content != original
    
    def _normalize_line_endings(self, content: str) -> str:
        """Ensure consistent line endings."""
        return content.replace('\r\n', '\n').replace('\r', '\n')
    
    def _format_import_section(self, content: str) -> str:
        """Ensure exactly one blank line after imports."""
        return self.config.IMPORT_SECTION.sub(r'\1\n', content)
    
    def _apply_class_spacing(self, content: str) -> str:
        """Apply single blank line before classes and functions."""
        content = self.config.CLASS_DEFINITION.sub(r'\n\n\1', content)
        content = self.config.FUNCTION_DEFINITION.sub(r'\n\n\1', content)
        return content
    
    def _remove_excessive_blanks(self, content: str) -> str:
        """Remove excessive blank lines (max 1 blank line)."""
        return self.config.EXCESSIVE_BLANKS.sub('\n\n', content)
    
    def _format_method_spacing(self, content: str) -> str:
        """Ensure proper spacing for methods inside classes."""
        lines = content.split('\n')
        result = []
        in_class = False
        class_indent = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('class ') and line.strip().endswith(':'):
                in_class, class_indent = True, len(line) - len(line.lstrip())
                result.append(line)
                continue
            
            if in_class and line.strip() and len(line) - len(line.lstrip()) <= class_indent:
                in_class = False
            
            if (in_class and line.strip().startswith('def ') and 
                i > 0 and result and result[-1].strip() and 
                not result[-1].strip().startswith('"""')):
                result.append('')
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _finalize_formatting(self, content: str) -> str:
        """Final cleanup - whitespace and file endings."""
        lines = [line.rstrip() for line in content.split('\n')]
        content = '\n'.join(lines).rstrip() + '\n'
        return self.config.EXCESSIVE_BLANKS.sub('\n\n', content)
    
    def process_file(self, file_path: Path, check_only: bool = False) -> bool:
        """Process a single file with precision formatting."""
        try:
            if not self._run_autopep8(file_path):
                return False
            
            content = file_path.read_text(encoding='utf-8')
            formatted_content, was_modified = self.format_content(content)
            
            self._stats["files_processed"] += 1
            
            if was_modified:
                if not check_only:
                    file_path.write_text(formatted_content, encoding='utf-8')
                    self._stats["files_modified"] += 1
                return not check_only
            
            return True
            
        except Exception as e:
            typer.echo(f"ERROR processing {file_path}: {e}", err=True)
            self._stats["errors"] += 1
            return False
    
    def _run_autopep8(self, file_path: Path) -> bool:
        """Execute autopep8 with optimal settings."""
        try:
            cmd = [
                sys.executable, "-m", "autopep8",
                f"--max-line-length={self.config.max_line_length}",
                "--ignore=E302,E305,E501",
                "--in-place",
                str(file_path)
            ]
            # Add aggressive flags (multiple flags for higher levels)
            for _ in range(self.config.aggressive_level):
                cmd.append("--aggressive")
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            typer.echo(f"ERROR: autopep8 failed for {file_path}: {e.stderr}", err=True)
            return False
    
    def get_stats(self) -> dict:
        """Return formatting statistics."""
        return self._stats.copy()


class FileDiscovery:
    """Efficient file discovery with smart filtering."""
    
    @staticmethod
    def find_python_files(path: Path, recursive: bool = True, 
                         exclude_patterns: Optional[Set[str]] = None) -> List[Path]:
        """Discover Python files with intelligent filtering."""
        exclude_patterns = exclude_patterns or FormattingConfig().excluded_patterns
        pattern = "**/*.py" if recursive else "*.py"
        
        return [
            file_path for file_path in path.glob(pattern)
            if not any(pattern in str(file_path) for pattern in exclude_patterns)
        ]


class OutputFormatter:
    """Elegant output formatting for user feedback."""
    
    @staticmethod
    def success(message: str) -> None:
        typer.echo(f"SUCCESS: {message}")
    
    @staticmethod
    def error(message: str) -> None:
        typer.echo(f"ERROR: {message}", err=True)
    
    @staticmethod
    def info(message: str) -> None:
        typer.echo(f"INFO: {message}")
    
    @staticmethod
    def report_stats(stats: dict, total_files: int) -> None:
        success_rate = (stats["files_processed"] - stats["errors"]) / total_files * 100
        typer.echo(f"\nFormatting Summary:")
        typer.echo(f"  Files processed: {stats['files_processed']}/{total_files}")
        typer.echo(f"  Files modified:  {stats['files_modified']}")
        typer.echo(f"  Success rate:    {success_rate:.1f}%")


@app.command()
def file(
    file_path: str = typer.Argument(..., help="Python file to format"),
    check: bool = typer.Option(False, "--check", "-c", help="Check formatting without modifying")
) -> None:
    """Format a single Python file with precision styling."""
    path = Path(file_path)
    
    if not path.exists():
        OutputFormatter.error(f"File not found: {file_path}")
        raise typer.Exit(1)
    
    if path.suffix != '.py':
        OutputFormatter.error(f"Not a Python file: {file_path}")
        raise typer.Exit(1)
    
    formatter = PrecisionFormatter()
    
    if check:
        OutputFormatter.info(f"Checking {file_path}...")
        if formatter.process_file(path, check_only=True):
            OutputFormatter.success(f"{file_path} is perfectly formatted")
        else:
            OutputFormatter.error(f"{file_path} needs formatting")
            raise typer.Exit(1)
    else:
        OutputFormatter.info(f"Formatting {file_path}...")
        if formatter.process_file(path):
            OutputFormatter.success(f"{file_path} formatted with precision")
        else:
            raise typer.Exit(1)


@app.command()
def directory(
    dir_path: str = typer.Argument("src", help="Directory to format"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r"),
    check: bool = typer.Option(False, "--check", "-c"),
    exclude: Optional[List[str]] = typer.Option(None, "--exclude", "-e")
) -> None:
    """Format all Python files in a directory with precision styling."""
    path = Path(dir_path)
    
    if not path.exists() or not path.is_dir():
        OutputFormatter.error(f"Directory not found: {dir_path}")
        raise typer.Exit(1)
    
    config = FormattingConfig()
    if exclude:
        config = FormattingConfig(excluded_patterns=config.excluded_patterns | set(exclude))
    
    files = FileDiscovery.find_python_files(path, recursive, config.excluded_patterns)
    
    if not files:
        OutputFormatter.info(f"No Python files found in {dir_path}")
        return
    
    OutputFormatter.info(f"Discovered {len(files)} Python files")
    formatter = PrecisionFormatter(config)
    
    failed_files = []
    needs_formatting = []
    
    with typer.progressbar(files, label="Processing files") as progress:
        for file_path in progress:
            result = formatter.process_file(file_path, check_only=check)
            if not result:
                if check:
                    needs_formatting.append(str(file_path))
                else:
                    failed_files.append(str(file_path))
    
    stats = formatter.get_stats()
    OutputFormatter.report_stats(stats, len(files))
    
    if check and needs_formatting:
        OutputFormatter.error(f"{len(needs_formatting)} files need formatting:")
        for file_path in needs_formatting[:5]:  # Show only first 5
            typer.echo(f"  • {file_path}")
        if len(needs_formatting) > 5:
            typer.echo(f"  ... and {len(needs_formatting) - 5} more")
        raise typer.Exit(1)
    
    if failed_files:
        OutputFormatter.error(f"Failed to format {len(failed_files)} files")
        raise typer.Exit(1)
    
    if not check:
        OutputFormatter.success("All files formatted with precision styling")


@app.command()
def all(check: bool = typer.Option(False, "--check", "-c")) -> None:
    """Format entire project with precision styling."""
    OutputFormatter.info("Applying precision formatting to entire project...")
    
    directories = ["src"]
    if Path("management").exists():
        directories.append("management")
    
    for dir_name in directories:
        try:
            directory(dir_name, recursive=True, check=check)
        except typer.Exit as e:
            if e.exit_code != 0:
                OutputFormatter.error(f"Formatting failed in {dir_name}/")
                raise
    
    if not check:
        OutputFormatter.success("Project formatted with precision styling")


if __name__ == "__main__":
    app()