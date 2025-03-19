"""Utility functions for handling resources."""
import os
import shutil
import importlib.resources
import logging
from pathlib import Path

def copy_tutorial_files(work_dir):
    """
    Copy tutorial files to the specified directory using importlib
    
    Args:
        work_dir (str): Target directory where tutorial files will be copied
    
    Returns:
        bool: True if copying was successful, False otherwise
    """
    print(f"Copying tutorial files to {work_dir}")
    success = True
    copied_files = []
    
    # Create the target directory if it doesn't exist
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        # Get the path to the examples directory using importlib.resources
        with importlib.resources.path('velrecover', 'examples') as tutorial_path:
            tutorial_dir = str(tutorial_path)
        
        print(f"Found example files at: {tutorial_dir}")
        
        if os.path.exists(tutorial_dir):
            # Copy the SEGY folder
            src_segy = os.path.join(tutorial_dir, "SEGY")
            dst_segy = os.path.join(work_dir, "SEGY")
            
            if os.path.exists(src_segy):
                print(f"Copying SEGY files from {src_segy}")
                os.makedirs(dst_segy, exist_ok=True)
                
                # List files before copying
                segy_files = os.listdir(src_segy)
                print(f"Found {len(segy_files)} files in SEGY directory: {', '.join(segy_files)}")
                
                for file in segy_files:
                    src_path = os.path.join(src_segy, file)
                    dst_path = os.path.join(dst_segy, file)
                    if os.path.isfile(src_path):
                        try:
                            shutil.copy2(src_path, dst_path)
                            copied_files.append(dst_path)
                            print(f"Copied: {file} ({os.path.getsize(dst_path)} bytes)")
                        except Exception as file_error:
                            print(f"Error copying {file}: {file_error}")
                            success = False
            else:
                print(f"SEGY source directory not found: {src_segy}")
                success = False
            
            # Copy the VELS folder with subfolders
            src_vels = os.path.join(tutorial_dir, "VELS")
            dst_vels = os.path.join(work_dir, "VELS")
            
            if os.path.exists(src_vels):
                print(f"Copying VELS directory from {src_vels}")
                
                # List subdirectories before copying
                vels_subdirs = [d for d in os.listdir(src_vels) 
                              if os.path.isdir(os.path.join(src_vels, d))]
                print(f"Found subdirectories in VELS: {', '.join(vels_subdirs)}")
                
                if os.path.exists(dst_vels):
                    print(f"Removing existing VELS directory: {dst_vels}")
                    shutil.rmtree(dst_vels)
                
                try:
                    shutil.copytree(src_vels, dst_vels)
                    
                    # Verify files were copied correctly
                    for root, _, files in os.walk(src_vels):
                        rel_path = os.path.relpath(root, src_vels)
                        for file in files:
                            src_file = os.path.join(root, file)
                            dst_file = os.path.join(dst_vels, rel_path, file)
                            if os.path.exists(dst_file):
                                copied_files.append(dst_file)
                                print(f"Copied: {os.path.join(rel_path, file)} ({os.path.getsize(dst_file)} bytes)")
                            else:
                                print(f"Failed to copy: {os.path.join(rel_path, file)}")
                                success = False
                except Exception as vels_error:
                    print(f"Error copying VELS directory: {vels_error}")
                    success = False
            else:
                print(f"VELS source directory not found: {src_vels}")
                success = False
                
            if success:
                print(f"Successfully copied {len(copied_files)} files from {tutorial_dir}")
            else:
                print(f"Some files were not copied correctly")
        else:
            print(f"Tutorial directory not found: {tutorial_dir}")
            success = False
    except Exception as e:
        print(f"Error accessing tutorial files: {e}")
        success = False
    
    # Summary
    if success and copied_files:
        print(f"All tutorial files copied successfully to {work_dir}")
    else:
        print(f"Some tutorial files could not be copied")
    
    return success