import re

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class MultiWindowRateThrottleMixin:
    """Allow DRF throttle rates like 5/5m in addition to 5/min."""

    def parse_rate(self, rate):
        if rate is None:
            return None, None

        num, period = rate.split('/')
        num_requests = int(num)
        match = re.fullmatch(r'(?P<count>\d+)?(?P<unit>[smhd]\w*)', period)
        if not match:
            return super().parse_rate(rate)

        multiplier = int(match.group('count') or 1)
        unit = match.group('unit')[0]
        duration = multiplier * {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
        }[unit]
        return num_requests, duration


class LoginRateThrottle(MultiWindowRateThrottleMixin, AnonRateThrottle):
    scope = 'login'


class RegisterRateThrottle(MultiWindowRateThrottleMixin, AnonRateThrottle):
    scope = 'register'


class PasswordResetRequestRateThrottle(MultiWindowRateThrottleMixin, AnonRateThrottle):
    scope = 'password_reset_request'


class ApplicationCreateRateThrottle(MultiWindowRateThrottleMixin, UserRateThrottle):
    scope = 'application_create'
