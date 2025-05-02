def is_valid_version(version_str: str) -> bool:
    """Check if a version string is valid"""

    # Empty string provided
    if not version_str or version_str.strip() == "":
        return False
    
    # Standard versioning pattern
    if re.match(f"^{version.VERSION_PATTERN}$", version_str, flags=re.IGNORECASE|re.VERBOSE):
        return True
    
    # Alphanumeric suffixes (e.g., "2.346.3_lts") and/or wildcards
    if re.match(r"^\d+(\.(\d+|\*))*((-|_)[a-z0-9_*]+)?$", version_str):
        return True

    return False

def _normalize_version_wildcard(ver_str: str) -> str:
    """
    Normalize version string by replacing '*x' with '0' for comparison
    
    Args:
        ver_str: Version string to normalize
        
    Returns:
        Normalized version string
    """
    # Replace 'x' wildcards with '0' for comparison purposes
    if '*' in ver_str:
        return re.sub(r"\*", '0', ver_str)
    return ver_str

def _compare_versions(ver1: str, operation: str, ver2: str) -> bool:
    """
    Compare two version strings with the specified operation
    Handles special version formats
    
    Args:
        ver1: First version string
        operation: Comparison operation ('<', '<=', '==', '>=', '>')
        ver2: Second version string
        
    Returns:
        Result of comparison
    """
    # Handle '*' wildcards in version strings
    if '*' in ver1 or 'x' in ver2:
        ver1_parts = ver1.split('.')
        ver2_parts = ver2.split('.')
        
        # Exact equality for wildcard versions
        if operation == '==':
            if len(ver1_parts) != len(ver2_parts):
                return False
            
            for i, (p1, p2) in enumerate(zip(ver1_parts, ver2_parts)):
                if p1 == '*' or p2 == '*':
                    continue
                if p1 != p2:
                    return False
            return True
            
        # Normalize to comparable versions
        ver1 = CVE._normalize_version_wildcard(ver1)
        ver2 = CVE._normalize_version_wildcard(ver2)
    
    # Try standard version comparison first
    try:
        v1 = version.parse(ver1)
        v2 = version.parse(ver2)
        
        if operation == '<':
            return v1 < v2
        elif operation == '<=':
            return v1 <= v2
        elif operation == '==':
            return v1 == v2
        elif operation == '>=':
            return v1 >= v2
        elif operation == '>':
            return v1 > v2
        else:
            return False
    except Exception:
        # Fall back to custom version comparison for special formats
        return CVE._custom_version_compare(ver1, operation, ver2)

def _custom_version_compare(ver1: str, operation: str, ver2: str) -> bool:
    """
    Custom version comparison for formats not supported by packaging.version
    
    Args:
        ver1: First version string
        operation: Comparison operation ('<', '<=', '==', '>=', '>')
        ver2: Second version string
        
    Returns:
        Result of comparison
    """
    # Split version and suffix
    def split_version_suffix(ver):
        match = re.match(r'^(\d+(?:\.\d+)*)[-_]?(.*)$', ver)
        if match:
            return match.group(1), match.group(2)
        return ver, ''
        
    v1, s1 = split_version_suffix(ver1)
    v2, s2 = split_version_suffix(ver2)
    
    # Split numeric parts
    try:
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        # Compare numeric parts
        for i in range(max(len(v1_parts), len(v2_parts))):
            p1 = v1_parts[i] if i < len(v1_parts) else 0
            p2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if p1 < p2:
                return operation in ['<', '<=']
            elif p1 > p2:
                return operation in ['>', '>=']
        
        # If there is a missing suffix
        if not s1 and not s2:
            return operation in ['==', '<=', '>=']
        elif not s1:
            return operation in ['<', '<=']
        elif not s2:
            return operation in ['>', '>=']

        # Compare suffixes
        if operation == '==':
            return s1 == s2
        elif operation == '<=':
            return s1 <= s2
        elif operation == '>=':
            return s1 >= s2
        elif operation == '<':
            return s1 < s2
        elif operation == '>':
            return s1 > s2
        
        return operation == '=='
    except Exception:
        # Last resort: lexicographical comparison
        if operation == '<':
            return ver1 < ver2
        elif operation == '<=':
            return ver1 <= ver2
        elif operation == '==':
            return ver1 == ver2
        elif operation == '>=':
            return ver1 >= ver2
        elif operation == '>':
            return ver1 > ver2
        else:
            return False

def version_included(self, ver_string: str) -> bool:
    """
    Check if a specific version is affected by this CVE
    
    Args:
        ver_string: Version string to check
        
    Returns:
        True if version is affected, False otherwise
    """
    if not ver_string or not self._data['cpe']:
        return False
        
    try:
        for cpe in self._data['cpe']:
            # Extract version from CPE if not wildcard
            cpe_parts = cpe['criteria'].split(":")
            if len(cpe_parts) < 6:
                continue
                
            cpe_ver_part = cpe_parts[5]
            
            # Global wildcard means potentially affected
            if cpe_ver_part == "*":
                return True
            
            # Handle '*' wildcards in CPE version
            if '*' in cpe_ver_part:
                ver_parts = ver_string.split('.')
                cpe_ver_parts = cpe_ver_part.split('.')
                
                # If CPE has fewer parts than the version string, pad with wildcards
                while len(cpe_ver_parts) < len(ver_parts):
                    cpe_ver_parts.append('*')
                
                # Check each component
                match = True
                for i, part in enumerate(cpe_ver_parts):
                    if i >= len(ver_parts):
                        break
                    if part != '*' and part != ver_parts[i]:
                        match = False
                        break
                
                if match:
                    return True
            
            # Exact match with CPE version
            if CVE.is_valid_version(cpe_ver_part):
                if CVE._compare_versions(ver_string, '==', cpe_ver_part):
                    return True
            
            # Range checks with enhanced version comparison
            try:
                # Including start and including end
                if (cpe.get("minVerIncluding") and cpe.get("maxVerIncluding") and CVE._compare_versions(cpe['minVerIncluding'], '<=', ver_string) and CVE._compare_versions(ver_string, '<=', cpe['maxVerIncluding'])):
                    return True
                    
                # Excluding start and excluding end
                if (cpe.get("minVerExcluding") and cpe.get("maxVerExcluding") and CVE._compare_versions(cpe['minVerExcluding'], '<', ver_string) and CVE._compare_versions(ver_string, '<', cpe['maxVerExcluding'])):
                    return True
                    
                # Including start and excluding end
                if (cpe.get("minVerIncluding") and cpe.get("maxVerExcluding") and CVE._compare_versions(cpe['minVerIncluding'], '<=', ver_string) and CVE._compare_versions(ver_string, '<', cpe['maxVerExcluding'])):
                    return True
                    
                # Excluding start and including end
                if (cpe.get("minVerExcluding") and cpe.get("maxVerIncluding") and CVE._compare_versions(cpe['minVerExcluding'], '<', ver_string) and CVE._compare_versions(ver_string, '<=', cpe['maxVerIncluding'])):
                    return True
                
                # Only min version specified (including)
                if cpe.get("minVerIncluding") and not any([cpe.get("maxVerIncluding"), cpe.get("maxVerExcluding")]):
                    if CVE._compare_versions(cpe['minVerIncluding'], '<=', ver_string):
                        return True
                        
                # Only min version specified (excluding)
                if cpe.get("minVerExcluding") and not any([cpe.get("maxVerIncluding"), cpe.get("maxVerExcluding")]):
                    if CVE._compare_versions(cpe['minVerExcluding'], '<', ver_string):
                        return True
                        
                # Only max version specified (including)
                if cpe.get("maxVerIncluding") and not any([cpe.get("minVerIncluding"), cpe.get("minVerExcluding")]):
                    if CVE._compare_versions(ver_string, '<=', cpe['maxVerIncluding']):
                        return True
                        
                # Only max version specified (excluding)
                if cpe.get("maxVerExcluding") and not any([cpe.get("minVerIncluding"), cpe.get("minVerExcluding")]):
                    if CVE._compare_versions(ver_string, '<', cpe['maxVerExcluding']):
                        return True
                        
            except Exception as e:
                self._logger.exception(f"Version comparison error for {ver_string} with {cpe}: {e}")
                # If any parsing fails, continue to next CPE
                continue
                
    except Exception as e:
        self._logger.exception(f"Error checking version inclusion for {ver_string}: {e}")
        return False
        
    return False