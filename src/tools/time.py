from datetime import datetime, timezone

def get_current_datetime():
    """
    Retrieves the current date, day of the week, and UTC time.
    
    The output provides a human-readable string that anchors the model to the current temporal context.
    
    Returns:
        str: A formatted string containing the Day, Date, and UTC Time.
             Example: "Tuesday, Feb 24, 2026 | 17:21 UTC"
    """
    now = datetime.now(timezone.utc)
    return now.strftime("%A, %b %d, %Y | %H:%M UTC")
