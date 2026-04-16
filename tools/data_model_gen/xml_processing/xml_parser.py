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
import xml.etree.ElementTree as ET

from .cluster_parser import ClusterParser
from .device_parser import DeviceParser
from .parse_context import load_cluster_parse_context
from utils.helper import write_to_file
from utils.exceptions import XmlParseError
from .yaml_parser import YamlParser
from utils.config import FileNames

logger = logging.getLogger(__name__)


def get_base_and_derived_cluster_files(input_dir):
    """Return (base_list, derived_list), each a list of (file_path, root).
    Parses each XML once; roots are reused by the cluster parser to avoid double parse.
    """
    base_cluster_files = []
    derived_cluster_files = []
    for file_name in os.listdir(input_dir):
        if os.path.isfile(
            os.path.join(input_dir, file_name)
        ) and not file_name.endswith(".xml"):
            logger.debug(f"Skipping {file_name} as it is not a valid file")
            continue
        file_path = os.path.join(input_dir, file_name)
        tree = ET.parse(file_path)
        root = tree.getroot()
        classification = root.find("classification")
        if (
            classification is not None
            and classification.get("hierarchy", "") == "derived"
        ):
            derived_cluster_files.append((file_path, root))
        else:
            base_cluster_files.append((file_path, root))
    return base_cluster_files, derived_cluster_files


def write_to_json_file(file_path, data):
    data_list = [item.to_dict() for item in data]
    data_list.sort(key=lambda x: int(x.get("id", "0"), 16))
    if not write_to_file(file_path, data_list, "json"):
        raise XmlParseError(
            "Failed to write JSON output",
            file_path=file_path,
            suggestion="Check write permissions and disk space.",
        )
    logger.info("GENERATED json at %s", file_path)
    return file_path


def process_cluster_files(
    input_dir,
    output_dir,
    yaml_file_path,
):
    """Process all cluster XML files from input directory and generate intermediate cluster json file.
    First it generates base cluster objects as during parsing of the derived cluster files, the base cluster objects are needed.
    Then it generates derived cluster objects.

    :param input_dir: Path to the directory containing the cluster XML files.
    :param output_dir: Path to the output directory.
    :returns: None

    """
    base_cluster_xml_files, derived_cluster_xml_files = (
        get_base_and_derived_cluster_files(input_dir)
    )
    if len(base_cluster_xml_files) == 0 and len(derived_cluster_xml_files) == 0:
        logger.error(f"No cluster XML files found in {input_dir}")
        return

    yaml_parser = YamlParser(yaml_file_path)

    cluster_parser = ClusterParser()
    context = load_cluster_parse_context(output_dir)
    base_clusters = []
    derived_clusters = []

    for file_path, root in base_cluster_xml_files:
        cluster_list = cluster_parser.parse(
            file_path=file_path,
            output_dir=output_dir,
            yaml_parser=yaml_parser,
            context=context,
            root=root,
        )
        if cluster_list is None or len(cluster_list) == 0:
            logger.error(
                "Processing of cluster file failed | File: %s",
                file_path,
            )
            continue
        base_clusters.extend(cluster_list)

    for file_path, root in derived_cluster_xml_files:
        cluster_list = cluster_parser.parse(
            file_path=file_path,
            output_dir=output_dir,
            base_clusters=base_clusters,
            yaml_parser=yaml_parser,
            context=context,
            root=root,
        )
        if cluster_list is None or len(cluster_list) == 0:
            logger.error(
                "Processing of derived cluster file failed | File: %s",
                file_path,
            )
            continue
        derived_clusters.extend(cluster_list)

    clusters = base_clusters + derived_clusters
    write_to_json_file(os.path.join(output_dir, FileNames.CLUSTER_JSON.value), clusters)


def process_device_files(input_dir, output_dir):
    """Process all device XML files from input directory and generate intermediate device json file.

    :param input_dir: Path to the directory containing the device XML files.
    :param output_dir: Path to the output directory.
    :returns: None

    """
    devices = []
    device_parser = DeviceParser()
    for file_name in os.listdir(input_dir):
        if os.path.isfile(os.path.join(input_dir, file_name)) and file_name.endswith(
            ".xml"
        ):
            file_path = os.path.join(input_dir, file_name)
            device = device_parser.parse(file_path=file_path)
            if device is not None:
                devices.append(device)

    write_to_json_file(os.path.join(output_dir, FileNames.DEVICE_JSON.value), devices)


def process_single_files(cluster_file, device_file, output_dir, yaml_file_path=None):
    """Process single cluster and device files and generate intermediate cluster and device json files.

    :param cluster_file: Path to the input cluster xml file to process.
    :param device_file: Path to the input device xml file to process.
    :param output_dir: Path to the output directory.
    :param yaml_file_path: Path to the yaml configuration file.
    :returns: None
    """
    clusters = []
    devices = []
    if cluster_file is not None:
        cluster_parser = ClusterParser()
        context = load_cluster_parse_context(output_dir)
        yaml_parser = YamlParser(yaml_file_path)
        # Base cluster objects not available for single file processing
        cluster_list = cluster_parser.parse(
            file_path=cluster_file,
            output_dir=output_dir,
            yaml_parser=yaml_parser,
            context=context,
        )
        if cluster_list is not None:
            clusters.extend(cluster_list)
    if device_file is not None:
        device_parser = DeviceParser()
        device = device_parser.parse(file_path=device_file)
        if device is not None:
            devices.append(device)

    write_to_json_file(os.path.join(output_dir, FileNames.CLUSTER_JSON.value), clusters)
    write_to_json_file(os.path.join(output_dir, FileNames.DEVICE_JSON.value), devices)
