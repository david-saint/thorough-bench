"""Task → YAML with block scalar formatting matching existing file style."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from mmce.harness.schema import Task


# Fields that should use block scalar style (|) for multi-line
_BLOCK_SCALAR_FIELDS = {"prompt"}

# Fields that should use folded scalar style (>-) for long single-concept text
_FOLDED_SCALAR_FIELDS = {
    "ambiguity",
    "wastefulness_boundary",
    "rationale",
    "anchor_reason",
}


class _BlockScalar(str):
    """String that serializes as YAML block scalar (|)."""


class _FoldedScalar(str):
    """String that serializes as YAML folded scalar (>-)."""


def _block_representer(dumper: yaml.Dumper, data: _BlockScalar) -> yaml.Node:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


def _folded_representer(dumper: yaml.Dumper, data: _FoldedScalar) -> yaml.Node:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=">")


class _TaskDumper(yaml.Dumper):
    """Custom YAML dumper with block/folded scalar support."""


_TaskDumper.add_representer(_BlockScalar, _block_representer)
_TaskDumper.add_representer(_FoldedScalar, _folded_representer)


def _apply_scalar_styles(data: dict, parent_key: str = "") -> dict:
    """Recursively apply block/folded scalar styles to string fields."""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            if key in _BLOCK_SCALAR_FIELDS:
                result[key] = _BlockScalar(value)
            elif key in _FOLDED_SCALAR_FIELDS and len(value) > 60:
                result[key] = _FoldedScalar(value)
            else:
                result[key] = value
        elif isinstance(value, dict):
            result[key] = _apply_scalar_styles(value, key)
        elif isinstance(value, list):
            result[key] = [
                _apply_scalar_styles(item, key) if isinstance(item, dict)
                else _BlockScalar(item) if isinstance(item, str) and key in _BLOCK_SCALAR_FIELDS
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def task_to_yaml(task: Task) -> str:
    """Serialize a Task to YAML string with proper formatting."""
    data = task.model_dump(mode="json", exclude_none=True)
    styled = _apply_scalar_styles(data)
    return yaml.dump(
        styled,
        Dumper=_TaskDumper,
        default_flow_style=False,
        sort_keys=False,
        width=88,
        allow_unicode=True,
    )


def write_task(task: Task, output_dir: str | Path) -> Path:
    """Write a Task to a YAML file in the appropriate dimension subdirectory."""
    output_dir = Path(output_dir)
    dim_dir = output_dir / task.dimension_alias
    dim_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{task.task_id}.yaml"
    path = dim_dir / filename

    yaml_content = task_to_yaml(task)
    path.write_text(yaml_content)

    return path


def next_task_number(output_dir: str | Path, dimension: str) -> int:
    """Find the next available task number for a dimension."""
    output_dir = Path(output_dir)
    dim_dir = output_dir / dimension

    if not dim_dir.exists():
        return 2  # Start at 2 since 001 is the exemplar

    max_num = 1  # Existing exemplar is 001
    pattern = re.compile(rf"{dimension}_st_(\d+)_")
    for yaml_path in dim_dir.glob("*.yaml"):
        match = pattern.match(yaml_path.stem)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)

    return max_num + 1
