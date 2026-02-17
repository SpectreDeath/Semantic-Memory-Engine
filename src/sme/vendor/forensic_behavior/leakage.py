from typing import Dict, Any

class LeakageAuditor:
    """
    Detects potential PII / credential leakage using fast validation logic.
    Optimized with __slots__.
    """
    __slots__ = ()

    def validate_luhn_checksum(self, numeric_string: str) -> Dict[str, Any]:
        """
        Validates a numeric string using the Luhn Algorithm (Mod 10).
        Useful for detecting mistakenly leaked credit card numbers, SSNs, or IDs.
        """
        # Remove common separators
        clean_str = "".join(filter(str.isdigit, numeric_string))
        
        if not clean_str:
            return {"is_valid": False, "status": "Invalid Input", "note": "No digits found"}

        try:
            digits = [int(d) for d in clean_str]
            # Double every second digit from the right
            for i in range(len(digits) - 2, -1, -2):
                doubled = digits[i] * 2
                if doubled > 9:
                    doubled -= 9
                digits[i] = doubled
            
            total_sum = sum(digits)
            is_valid = (total_sum % 10 == 0)
            
            return {
                "is_valid": is_valid,
                "digit_count": len(clean_str),
                "check_digit": int(clean_str[-1]),
                "status": "Success"
            }
        except Exception as e:
            return {"error": str(e), "status": "Error"}

def validate_luhn_checksum(numeric_string: str) -> Dict[str, Any]:
    """Standalone wrapper for Luhn validation."""
    auditor = LeakageAuditor()
    return auditor.validate_luhn_checksum(numeric_string)
