# Copyright 2026 Espressif Systems (Shanghai) PTE LTD
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import logging
import subprocess
from utils.config import ARTIFACTS_DIR, FileNames
from utils.helper import write_to_file
from utils.exceptions import ConfigurationError, CodeGenerationError
from chip_source_deps.cluster_mapping import normalize_cluster_name
from chip_source_deps.cluster_mapping import (
    generate_delegate_cluster_mapping,
    generated_plugin_init_cb_cluster_mapping,
)
from chip_source_deps.zap_filter import generate_zap_filter_list
from chip_source_deps.internally_managed_attributes import (
    generate_internally_managed_attributes,
)

logger = logging.getLogger(__name__)


def _find_migrated_cluster_dirs(root_dir: str) -> set[str]:
    """Return the set of top-level cluster directories under ``root_dir`` that
    contain a header declaring a class inheriting ``DefaultServerCluster``.
    """
    result = subprocess.run(
        ["grep", "-rl", "--include=*.h", "public DefaultServerCluster", root_dir],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode >= 2:
        raise RuntimeError(f"grep failed ({result.returncode}): {result.stderr}")

    abs_root = os.path.abspath(root_dir)
    cluster_dirs: set[str] = set()
    for header_path in result.stdout.splitlines():
        rel = os.path.relpath(header_path, abs_root)
        top = rel.split(os.sep, 1)[0]
        if top and top != "..":
            cluster_dirs.add(os.path.join(abs_root, top))
    return cluster_dirs


def generate_migrated_clusters(root_dir) -> tuple[bool, str]:
    """Find all migrated clusters and write them to ``Artifacts/migrated_clusters.json``.

    The JSON holds two lists:
      - ``migrated_cluster``: clusters using ``DefaultServerCluster`` at the
        cluster top level; these feed data_model_gen.
      - ``migrated_cluster_with_codegen_impl``: clusters that own a ``codegen/``
        subdir; they have legacy implementation as it is and are skipped by data_model_gen.

    Args:
        root_dir: The root directory to search in.
    Returns:
        True if successful, False otherwise
    """
    migrated_clusters = set()
    migrated_clusters_with_codegen_impl = set()

    try:
        for cluster_dir in _find_migrated_cluster_dirs(root_dir):
            cluster_name = normalize_cluster_name(os.path.basename(cluster_dir))
            if not cluster_name:
                continue
            if os.path.isdir(os.path.join(cluster_dir, "codegen")):
                migrated_clusters_with_codegen_impl.add(cluster_name)
            else:
                migrated_clusters.add(cluster_name)

        payload = {
            "migrated_cluster": sorted(migrated_clusters),
            "migrated_cluster_with_codegen_impl": sorted(
                migrated_clusters_with_codegen_impl
            ),
        }

        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        artifact_path = os.path.join(ARTIFACTS_DIR, FileNames.MIGRATED_CLUSTERS.value)

        if write_to_file(artifact_path, payload, "json"):
            logger.info(f"Successfully written Migrated Clusters to {artifact_path}")
            return True, None
        return False, f"Error writing to {artifact_path}"
    except Exception as e:
        return False, f"Error generating migrated clusters: {str(e)}"


def generate_requirements(esp_matter_path, output_dir):
    """
    Generate all the required intermediate server files

    Args:
        esp_matter_path: Path to the ESP Matter repository
        output_dir: Directory where the generated files will be stored
    Returns:
        True if successful, False otherwise
    """
    os.makedirs(output_dir, exist_ok=True)

    chip_dir = os.path.join(esp_matter_path, "connectedhomeip/connectedhomeip")
    root_cluster_server_dir = os.path.join(chip_dir, "src/app/clusters/")
    header_files_dir = os.path.join(chip_dir, "zzz_generated/app-common/clusters")
    plugin_cb_header_file = os.path.join(
        esp_matter_path,
        "components/esp_matter/zap_common/app/PluginApplicationCallbacks.h",
    )

    if not os.path.exists(root_cluster_server_dir):
        raise ConfigurationError(
            "Clusters directory does not exist",
            file_path=root_cluster_server_dir,
            context="generate_requirements",
            suggestion="Ensure connectedhomeip is checked out under esp_matter_path.",
        )

    if not os.path.exists(header_files_dir):
        raise ConfigurationError(
            "Header files directory does not exist",
            file_path=header_files_dir,
            context="generate_requirements",
            suggestion="Generate CHIP app-common headers (zzz_generated) first.",
        )

    if not os.path.exists(plugin_cb_header_file):
        raise ConfigurationError(
            "Plugin callback header file does not exist",
            file_path=plugin_cb_header_file,
            context="generate_requirements",
            suggestion="Ensure esp_matter components include zap_common/app/PluginApplicationCallbacks.h.",
        )

    file_paths = {
        FileNames.INTERNALLY_MANAGED_ATTRIBUTES: os.path.join(
            output_dir, FileNames.INTERNALLY_MANAGED_ATTRIBUTES.value
        ),
        FileNames.DELEGATE_CLUSTERS: os.path.join(
            output_dir, FileNames.DELEGATE_CLUSTERS.value
        ),
        FileNames.PLUGIN_INIT_CB_CLUSTERS: os.path.join(
            output_dir, FileNames.PLUGIN_INIT_CB_CLUSTERS.value
        ),
        FileNames.ZAP_FILTER_LIST: os.path.join(
            output_dir, FileNames.ZAP_FILTER_LIST.value
        ),
    }

    logger.debug(
        "Generating internally managed attributes from both server files and zcl.json..."
    )
    zcl_json_path = os.path.join(chip_dir, "src/app/zap-templates/zcl/zcl.json")
    if not os.path.exists(zcl_json_path):
        raise ConfigurationError(
            "zcl.json file does not exist",
            file_path=zcl_json_path,
            context="generate_requirements",
            suggestion="Ensure connectedhomeip zap-templates are present.",
        )
    is_generated, error_message = generate_internally_managed_attributes(
        root_cluster_server_dir,
        zcl_json_path,
        file_paths[FileNames.INTERNALLY_MANAGED_ATTRIBUTES],
    )
    if not is_generated:
        raise CodeGenerationError(
            error_message,
            file_path=file_paths[FileNames.INTERNALLY_MANAGED_ATTRIBUTES],
            context="generate_requirements",
            suggestion="Check CHIP cluster server sources and zcl.json format.",
        )

    logger.debug("Generating delegate clusters...")
    is_generated, error_message = generate_delegate_cluster_mapping(
        root_cluster_server_dir, file_paths[FileNames.DELEGATE_CLUSTERS]
    )
    if not is_generated:
        raise CodeGenerationError(
            error_message,
            file_path=file_paths[FileNames.DELEGATE_CLUSTERS],
            context="generate_requirements",
            suggestion=f"Check {root_cluster_server_dir} and write permissions.",
        )

    logger.debug("Generating plugin init callback clusters...")
    is_generated, error_message = generated_plugin_init_cb_cluster_mapping(
        plugin_cb_header_file, file_paths[FileNames.PLUGIN_INIT_CB_CLUSTERS]
    )
    if not is_generated:
        raise CodeGenerationError(
            error_message,
            file_path=file_paths[FileNames.PLUGIN_INIT_CB_CLUSTERS],
            context="generate_requirements",
            suggestion=f"Check {plugin_cb_header_file} and output path.",
        )

    logger.debug("Generating include list...")
    is_generated, error_message = generate_zap_filter_list(
        header_files_dir, file_paths[FileNames.ZAP_FILTER_LIST]
    )
    if not is_generated:
        raise CodeGenerationError(
            error_message,
            file_path=file_paths[FileNames.ZAP_FILTER_LIST],
            context="generate_requirements",
            suggestion=f"Check {header_files_dir} and write permissions.",
        )

    logger.debug("Finding migrated clusters...")
    is_generated, error_message = generate_migrated_clusters(root_cluster_server_dir)
    if not is_generated:
        raise CodeGenerationError(
            error_message,
            file_path=os.path.join(ARTIFACTS_DIR, FileNames.MIGRATED_CLUSTERS.value),
            context="generate_requirements",
            suggestion=f"Check {root_cluster_server_dir} and write permissions.",
        )

    return True
