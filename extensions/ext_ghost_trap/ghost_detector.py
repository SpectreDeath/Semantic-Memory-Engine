"""
Ghost Trap Extension - Ghost Detector

Provides the scan_for_ghosts() tool to detect unauthorized large .bin or .json files
that might contain hidden model weights or other suspicious data.
"""

import os
import sys
import logging
import threading
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime

# Configure logging for the ghost detector
logger = logging.getLogger('ghost_trap.ghost_detector')
logger.setLevel(logging.INFO)

# Create file handler for ghost detection events
ghost_detector_handler = logging.FileHandler('ghost_detection_events.log')
ghost_detector_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ghost_detector_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(ghost_detector_handler)


@dataclass
class GhostFile:
    """Represents a detected ghost file."""
    path: str
    size_mb: float
    file_type: str
    is_hidden: bool
    last_modified: datetime
    suspicious_indicators: List[str]


class GhostDetector:
    """Detects unauthorized large files that might be hidden model weights."""
    
    def __init__(self, project_root: Optional[str] = None, size_threshold_mb: int = 100):
        """
        Initialize the ghost detector.
        
        Args:
            project_root: Root directory to scan. If None, uses current working directory.
            size_threshold_mb: Minimum file size in MB to consider as suspicious.
        """
        self.project_root = Path(project_root or os.getcwd()).resolve()
        self.size_threshold_bytes = size_threshold_mb * 1024 * 1024  # Convert MB to bytes
        self.target_extensions = {'.bin', '.json'}
        self.suspicious_patterns = {
            'model_weights': ['model', 'weight', 'checkpoint', 'param'],
            'hidden_indicators': ['hidden', 'secret', 'private', 'internal'],
            'suspicious_names': ['ghost', 'trap', 'monitor', 'surveillance']
        }
        
    def _get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in megabytes."""
        try:
            return file_path.stat().st_size / (1024 * 1024)
        except OSError:
            return 0.0
    
    def _is_hidden_file(self, file_path: Path) -> bool:
        """Check if a file is hidden."""
        # Check for dot-prefixed files/directories
        for part in file_path.parts:
            if part.startswith('.') and len(part) > 1:  # Exclude '.' and '..'
                return True
        
        # On Windows, check file attributes
        if sys.platform == 'win32':
            try:
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
                return attrs != -1 and attrs & 2  # FILE_ATTRIBUTE_HIDDEN = 2
            except (AttributeError, ImportError):
                pass
        
        return False
    
    def _analyze_file_name(self, file_path: Path) -> List[str]:
        """Analyze file name for suspicious indicators."""
        indicators = []
        file_name_lower = file_path.name.lower()
        
        # Check for suspicious patterns
        for category, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                if pattern in file_name_lower:
                    indicators.append(f"{category}: {pattern}")
        
        # Check if file is in a hidden directory
        if self._is_hidden_file(file_path.parent):
            indicators.append("hidden_directory")
        
        return indicators
    
    def _should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned."""
        # Skip if not target extension
        if file_path.suffix.lower() not in self.target_extensions:
            return False
        
        # Skip if too small
        if self._get_file_size_mb(file_path) < (self.size_threshold_bytes / (1024 * 1024)):
            return False
        
        return True
    
    def scan_directory(self, directory: Optional[str] = None, recursive: bool = True) -> List[GhostFile]:
        """
        Scan a directory for ghost files.
        
        Args:
            directory: Directory to scan. If None, uses project root.
            recursive: Whether to scan subdirectories recursively.
            
        Returns:
            List of detected ghost files.
        """
        scan_dir = Path(directory or self.project_root).resolve()
        ghost_files = []
        
        logger.info(f"Starting ghost scan in: {scan_dir}")
        print(f"🔍 Scanning for ghost files in: {scan_dir}")
        
        try:
            if recursive:
                files_to_scan = [f for f in scan_dir.rglob('*') if f.is_file()]
            else:
                files_to_scan = [f for f in scan_dir.iterdir() if f.is_file()]
            
            for file_path in files_to_scan:
                if self._should_scan_file(file_path):
                    size_mb = self._get_file_size_mb(file_path)
                    is_hidden = self._is_hidden_file(file_path)
                    suspicious_indicators = self._analyze_file_name(file_path)
                    
                    ghost_file = GhostFile(
                        path=str(file_path),
                        size_mb=size_mb,
                        file_type=file_path.suffix.lower(),
                        is_hidden=is_hidden,
                        last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
                        suspicious_indicators=suspicious_indicators
                    )
                    
                    ghost_files.append(ghost_file)
                    
                    # Log and display the detection
                    message = (
                        f"SUSPICIOUS FILE DETECTED - "
                        f"Path: {file_path}, "
                        f"Size: {size_mb:.2f}MB, "
                        f"Type: {file_path.suffix}, "
                        f"Hidden: {is_hidden}, "
                        f"Indicators: {', '.join(suspicious_indicators) if suspicious_indicators else 'None'}"
                    )
                    
                    logger.warning(message)
                    print(f"👻 {message}")
        
        except PermissionError as e:
            logger.error(f"Permission denied scanning {scan_dir}: {e}")
            print(f"⚠️  Permission denied scanning {scan_dir}: {e}")
        except Exception as e:
            logger.error(f"Error during ghost scan: {e}")
            print(f"❌ Error during ghost scan: {e}")
        
        logger.info(f"Ghost scan completed. Found {len(ghost_files)} suspicious files.")
        print(f"✅ Scan completed. Found {len(ghost_files)} suspicious files.")
        
        return ghost_files
    
    def generate_report(self, ghost_files: List[GhostFile]) -> Dict[str, Any]:
        """Generate a summary report of ghost detection results."""
        if not ghost_files:
            return {
                'status': 'clean',
                'message': 'No suspicious files detected.',
                'total_files_scanned': 0,
                'suspicious_files': []
            }
        
        # Sort by size (largest first)
        ghost_files.sort(key=lambda x: x.size_mb, reverse=True)
        
        # Generate summary statistics
        total_size = sum(f.size_mb for f in ghost_files)
        hidden_count = sum(1 for f in ghost_files if f.is_hidden)
        
        report = {
            'status': 'suspicious_activity_detected',
            'message': f'Found {len(ghost_files)} potentially unauthorized files.',
            'scan_summary': {
                'total_suspicious_files': len(ghost_files),
                'total_suspicious_size_mb': round(total_size, 2),
                'hidden_files_count': hidden_count,
                'largest_file_mb': round(ghost_files[0].size_mb, 2) if ghost_files else 0
            },
            'suspicious_files': [
                {
                    'path': f.path,
                    'size_mb': round(f.size_mb, 2),
                    'file_type': f.file_type,
                    'is_hidden': f.is_hidden,
                    'last_modified': f.last_modified.isoformat(),
                    'suspicious_indicators': f.suspicious_indicators
                }
                for f in ghost_files
            ]
        }
        
        return report
    
    def print_detailed_report(self, ghost_files: List[GhostFile]):
        """Print a detailed report of ghost detection results."""
        if not ghost_files:
            print("✅ No suspicious files detected in the scan.")
            return
        
        print("\n" + "="*80)
        print("GHOST DETECTION DETAILED REPORT")
        print("="*80)
        
        for i, ghost_file in enumerate(ghost_files, 1):
            print(f"\n{i}. File: {ghost_file.path}")
            print(f"   Size: {ghost_file.size_mb:.2f} MB")
            print(f"   Type: {ghost_file.file_type}")
            print(f"   Hidden: {ghost_file.is_hidden}")
            print(f"   Last Modified: {ghost_file.last_modified}")
            if ghost_file.suspicious_indicators:
                print(f"   Suspicious Indicators: {', '.join(ghost_file.suspicious_indicators)}")
            else:
                print("   Suspicious Indicators: None detected")
        
        print("\n" + "="*80)
        print("END OF REPORT")
        print("="*80)


def scan_for_ghosts(project_root: Optional[str] = None, size_threshold_mb: int = 100, 
                   recursive: bool = True, detailed_report: bool = True) -> Dict[str, Any]:
    """
    Main function to scan for ghost files.
    
    Args:
        project_root: Root directory to scan. If None, uses current working directory.
        size_threshold_mb: Minimum file size in MB to consider as suspicious.
        recursive: Whether to scan subdirectories recursively.
        detailed_report: Whether to print a detailed report.
        
    Returns:
        Dictionary containing scan results and summary.
    """
    detector = GhostDetector(project_root=project_root, size_threshold_mb=size_threshold_mb)
    ghost_files = detector.scan_directory(recursive=recursive)
    
    report = detector.generate_report(ghost_files)
    
    if detailed_report:
        detector.print_detailed_report(ghost_files)
    
    return report


# Export the main function for use as a tool
__all__ = ['scan_for_ghosts', 'GhostDetector', 'GhostFile']