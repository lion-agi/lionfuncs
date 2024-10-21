import logging

from .algo.cosine_similarity import cosine_similarity
from .algo.hamming_similarity import hamming_similarity
from .algo.jaro_distance import jaro_winkler_similarity
from .algo.levenshtein_distance import levenshtein_similarity
from .data.flatten import flatten
from .data.nfilter import nfilter
from .data.nget import nget
from .data.ninsert import ninsert
from .data.nmerge import nmerge
from .data.npop import npop
from .data.nset import nset
from .data.to_dict import to_dict
from .data.to_list import to_list
from .data.to_num import to_num
from .data.to_str import to_str
from .data.unflatten import unflatten
from .data.utils import is_homogeneous, is_same_dtype, is_structure_homogeneous
from .file.chunk_by_chars import chunk_by_chars
from .file.chunk_by_tokens import chunk_by_tokens
from .file.chunk_content import chunk_content
from .file.clear_path import clear_path
from .file.copy_file import copy_file
from .file.create_path import create_path
from .file.dir_to_files import dir_to_files
from .file.file_to_chunks import file_to_chunks
from .file.get_file_size import get_file_size
from .file.is_valid_path import is_valid_path
from .file.list_files import list_files
from .file.read_file import read_file
from .file.save_to_file import save_to_file
from .file.split_path import split_path
from .func.bcall import bcall
from .func.call_decorator import CallDecorator
from .func.lcall import alcall, lcall
from .func.mcall import mcall
from .func.pcall import pcall
from .func.rcall import rcall
from .func.tcall import tcall
from .func.ucall import ucall
from .func.utils import force_async
from .integrations.pandas_ import read_csv, read_json, to_csv, to_df, to_excel
from .integrations.pydantic_ import break_down_pydantic_annotation, new_model
from .ln_undefined import LN_UNDEFINED, LionUndefinedType
from .note import Note, note
from .package.check_import import check_import
from .package.get_cpu_architecture import get_cpu_architecture
from .package.install_import import install_import
from .package.is_import_installed import is_import_installed
from .package.list_installed_packages import list_installed_packages
from .package.uninstall_package import uninstall_package
from .package.update_package import update_package
from .parse.as_readable_json import as_readable_json
from .parse.choose_most_similar import choose_most_similar
from .parse.extract_code_block import extract_code_block
from .parse.extract_json_block import extract_block
from .parse.extract_json_schema import (
    extract_json_schema,
    json_schema_to_cfg,
    json_schema_to_regex,
    print_cfg,
)
from .parse.function_to_schema import function_to_schema
from .parse.fuzzy_parse_json import fuzzy_parse_json
from .parse.md_to_json import md_to_json
from .parse.validate_boolean import validate_boolean
from .parse.validate_mapping import validate_mapping
from .parse.xml_parser import dict_to_xml, xml_to_dict
from .utils import (
    copy,
    format_deprecation_msg,
    get_bins,
    get_class_file_registry,
    get_class_objects,
    get_file_classes,
    insert_random_hyphens,
    is_same_dtype,
    run_pip_command,
    time,
    unique_hash,
)
from .version import __version__

logging.basicConfig(level=logging.INFO)

__all__ = [
    "cosine_similarity",
    "hamming_similarity",
    "jaro_winkler_similarity",
    "levenshtein_similarity",
    "flatten",
    "nfilter",
    "nget",
    "ninsert",
    "nmerge",
    "npop",
    "nset",
    "to_dict",
    "to_list",
    "to_num",
    "to_str",
    "unflatten",
    "is_homogeneous",
    "is_same_dtype",
    "is_structure_homogeneous",
    "chunk_by_chars",
    "chunk_by_tokens",
    "chunk_content",
    "clear_path",
    "copy_file",
    "create_path",
    "dir_to_files",
    "file_to_chunks",
    "get_file_size",
    "is_valid_path",
    "list_files",
    "read_file",
    "save_to_file",
    "split_path",
    "bcall",
    "CallDecorator",
    "alcall",
    "lcall",
    "mcall",
    "pcall",
    "rcall",
    "tcall",
    "ucall",
    "force_async",
    "to_df",
    "to_csv",
    "read_csv",
    "read_json",
    "to_excel",
    "break_down_pydantic_annotation",
    "new_model",
    "as_readable_json",
    "choose_most_similar",
    "extract_code_block",
    "extract_block",
    "extract_json_schema",
    "json_schema_to_regex",
    "json_schema_to_cfg",
    "print_cfg",
    "function_to_schema",
    "md_to_json",
    "validate_boolean",
    "validate_mapping",
    "xml_to_dict",
    "dict_to_xml",
    "fuzzy_parse_json",
    "note",
    "Note",
    "format_deprecation_msg",
    "unique_hash",
    "insert_random_hyphens",
    "get_file_classes",
    "get_class_file_registry",
    "get_class_objects",
    "time",
    "copy",
    "run_pip_command",
    "format_deprecation_msg",
    "get_bins",
    "LN_UNDEFINED",
    "LionUndefinedType",
    "__version__",
    "get_cpu_architecture",
    "check_import",
    "install_import",
    "is_import_installed",
    "uninstall_package",
    "list_installed_packages",
    "update_package",
]
