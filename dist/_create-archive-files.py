#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import json
import shutil
import pathlib
import requests
from sys import argv, stderr

archive_types = {
    'tag': 'tags',
    'category': 'categories'
}

input_options = ['delete_archives', 'delete_archives_folder']

def create_front_matter(archive_s_form, archive_p_form, archive_item_value, archive_value_escaped):
    front_matter_template = f'''---
title: "{archive_item_value}"
type: {archive_s_form}
{archive_s_form}: {archive_item_value}
layout: archive-{archive_p_form}
---
'''
    return front_matter_template

def safe_filename(original_name):
    """安全处理文件名（保留中文）"""
    name = re.sub(r'#', 'sharp', original_name)
    name = re.sub(r'[\\/:*?"<>|\s]', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name or "untitled"

def delete_folder(folder_path, out_message):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(out_message, folder_path)
        return True
    print('文件夹不存在:', folder_path)
    return False

def main():
    if len(argv) < 2:
        print("Usage: {} archive_url archive_folder_path".format(argv[0]), file=stderr)
        exit(1)

    archive_data_url = argv[1]
    archive_folder_path = argv[2]

    if archive_data_url in input_options:
        delete_success = True
        if archive_data_url == input_options[1]:
            delete_success = delete_folder(archive_folder_path, '已删除目录:')
        else:
            for arch_type in archive_types.values():
                folder_path = os.path.join(archive_folder_path, arch_type)
                delete_success &= delete_folder(folder_path, '已删除文件:')
        exit(0 if delete_success else 1)

    try:
        response = requests.get(archive_data_url)
        response.raise_for_status()
        json_data = response.json()
    except Exception as e:
        print('获取或解析数据失败:', str(e))
        exit(1)

    added_files = []
    removed_files = []
    
    for arch_type, archive_type in archive_types.items():
        file_list = []
        archive_dir = os.path.join(archive_folder_path, archive_type)
        pathlib.Path(archive_dir).mkdir(parents=True, exist_ok=True)
        
        for archive_value in list(set(json_data[archive_type])):
            try:
                file_name = safe_filename(archive_value) + '.md'
                file_path = os.path.join(archive_dir, file_name)
                
                front_matter = create_front_matter(
                    arch_type, archive_type, archive_value, file_name)
                
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(front_matter)
                    added_files.append(f'{archive_type}/{file_name}')
                
                file_list.append(file_name)
            except Exception as e:
                print(f'处理 {archive_value} 时出错:', str(e))
        
        for existing_file in os.listdir(archive_dir):
            if existing_file not in file_list:
                os.remove(os.path.join(archive_dir, existing_file))
                removed_files.append(f'{archive_type}/{existing_file}')

    print('\n操作结果:')
    print(f'新增文件: {len(added_files)}个')
    for file in added_files:
        print(f'  + {file}')
    
    print(f'\n移除文件: {len(removed_files)}个')
    for file in removed_files:
        print(f'  - {file}')

if __name__ == '__main__':
    main()