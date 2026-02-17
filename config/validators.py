from django.core.validators import RegexValidator


MOBILE_NUMBER_PATTERN = r"^[6-9]\d{9}$"
MOBILE_NUMBER_ERROR = "Enter a valid 10-digit mobile number starting with 6, 7, 8, or 9."

mobile_number_validator = RegexValidator(
    regex=MOBILE_NUMBER_PATTERN,
    message=MOBILE_NUMBER_ERROR,
)
