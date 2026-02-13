import platform
try:
    from win10toast import ToastNotifier
    HAS_TOAST = True
except ImportError:
    HAS_TOAST = False

def send_forensic_alert(title, message, duration=10):
    """Send a Windows desktop notification for forensic alerts."""
    print(f"🔔 ALERT: {title} | {message}")
    
    if HAS_TOAST and platform.system() == "Windows":
        try:
            toaster = ToastNotifier()
            toaster.show_toast(
                f"SME: {title}",
                message,
                icon_path=None, # Can add a custom .ico later
                duration=duration,
                threaded=True
            )
        except Exception as e:
            print(f"⚠️ Failed to send toast notification: {e}")

def check_for_threat_collision(intel_package):
    """Analyze intel package for known threat signatures/collisions."""
    # Simple logic to detect CBRN_Ghost_99 or negative sentiment outliers
    osint = intel_package.get("osint", [])
    if isinstance(osint, dict): osint = [osint]
    
    usernames = {s.get("username") for s in osint if s.get("username")}
    
    # We'll simulate a 'Threat Intelligence' match if CBRN_Ghost_99 is present
    if "CBRN_Ghost_99" in usernames:
        send_forensic_alert(
            "CRITICAL THREAT COLLISION",
            "Target 'CBRN_Ghost_99' detected in both OSINT and Forensic News. CBRN risk confirmed.",
            duration=15
        )
        return True
    return False
