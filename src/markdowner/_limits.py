# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""
Security limits and configuration for MarkDowner.

Provides configurable limits for input size, zip handling, and recursion depth
to prevent DoS attacks via malicious files.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Limits:
    """
    Security limits for MarkDowner.

    These limits help prevent DoS attacks via malicious or oversized files.
    """

    # Maximum input size in bytes (default: 100MB)
    max_input_bytes: int = 100 * 1024 * 1024

    # Maximum number of entries in a ZIP archive
    max_zip_entries: int = 1000

    # Maximum total uncompressed size of ZIP archive (default: 200MB)
    max_zip_total_uncompressed_bytes: int = 200 * 1024 * 1024

    # Maximum size of a single ZIP entry (default: 50MB)
    max_zip_entry_bytes: int = 50 * 1024 * 1024

    # Maximum recursion depth for nested archives
    max_recursion_depth: int = 3

    # Enabled flag - when False, limits are not enforced
    enabled: bool = True

    def check_input_size(self, size: int) -> bool:
        """Check if input size is within limits."""
        if not self.enabled:
            return True
        return size <= self.max_input_bytes

    def check_zip_entry_count(self, count: int) -> bool:
        """Check if number of ZIP entries is within limits."""
        if not self.enabled:
            return True
        return count <= self.max_zip_entries

    def check_zip_total_size(self, size: int) -> bool:
        """Check if total ZIP uncompressed size is within limits."""
        if not self.enabled:
            return True
        return size <= self.max_zip_total_uncompressed_bytes

    def check_zip_entry_size(self, size: int) -> bool:
        """Check if a single ZIP entry size is within limits."""
        if not self.enabled:
            return True
        return size <= self.max_zip_entry_bytes

    def check_recursion_depth(self, depth: int) -> bool:
        """Check if recursion depth is within limits."""
        if not self.enabled:
            return True
        return depth <= self.max_recursion_depth


# Global default limits instance
DEFAULT_LIMITS = Limits()


def create_custom_limits(
    max_input_bytes: Optional[int] = None,
    max_zip_entries: Optional[int] = None,
    max_zip_total_uncompressed_bytes: Optional[int] = None,
    max_zip_entry_bytes: Optional[int] = None,
    max_recursion_depth: Optional[int] = None,
    enabled: bool = True,
) -> Limits:
    """Create a custom Limits instance with specified overrides."""
    return Limits(
        max_input_bytes=max_input_bytes or DEFAULT_LIMITS.max_input_bytes,
        max_zip_entries=max_zip_entries or DEFAULT_LIMITS.max_zip_entries,
        max_zip_total_uncompressed_bytes=(
            max_zip_total_uncompressed_bytes
            or DEFAULT_LIMITS.max_zip_total_uncompressed_bytes
        ),
        max_zip_entry_bytes=max_zip_entry_bytes or DEFAULT_LIMITS.max_zip_entry_bytes,
        max_recursion_depth=max_recursion_depth or DEFAULT_LIMITS.max_recursion_depth,
        enabled=enabled,
    )