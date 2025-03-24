#!/bin/bash

# 定义包含 docker-compose.yml 文件的子文件夹列表
compose_folders=("crates/catalog/glue/testdata/glue_catalog" "crates/catalog/hms/testdata/hms_catalog" "crates/iceberg/testdata/file_io_s3" "crates/integrations/datafusion/testdata" "crates/catalog/rest/testdata/rest_catalog")

# 遍历每个子文件夹并启动 docker-compose 服务
for folder in "${compose_folders[@]}"; do
  echo "Starting docker-compose services in $folder"
  (cd $folder && docker-compose down && docker-compose up -d)
  if [ $? -ne 0 ]; then
    echo "Failed to start docker-compose services in $folder"
    exit 1
  fi
done

echo "All docker-compose services are started."