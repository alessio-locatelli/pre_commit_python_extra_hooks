"""Test fixture: Python code with descriptive variable names (should pass)."""


def calculate_total(invoice_items):
    """Calculate total from invoice items."""
    total_amount = 0
    for item in invoice_items:
        total_amount += item.price * item.quantity
    return total_amount


def process_user_records(user_records):
    """Process user records and return transformed output."""
    transformed_output = []
    for record in user_records:
        transformed_output.append(record.name.upper())
    return transformed_output


class UserProcessor:
    """Example class with descriptive variable names."""

    def __init__(self, configuration):
        """Initialize with configuration."""
        self.configuration = configuration

    def fetch_users(self):
        """Fetch users from database."""
        user_list = []
        return user_list
