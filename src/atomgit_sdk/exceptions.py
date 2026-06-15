"""
Custom exceptions for AtomGit SDK
"""



class AtomGitSDKError(Exception):
    """Base exception for AtomGit SDK"""

    pass


class AtomGitAPIError(AtomGitSDKError):
    """Exception raised for AtomGit API errors"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"AtomGit API Error ({self.status_code}): {self.message}"
        return f"AtomGit API Error: {self.message}"


class ConfigurationError(AtomGitSDKError):
    """Exception raised for configuration errors"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"Configuration Error: {self.message}"


class DiffParseError(AtomGitSDKError):
    """Exception raised for diff parsing errors"""

    def __init__(self, message: str, patch_content: str | None = None):
        self.message = message
        self.patch_content = patch_content
        super().__init__(self.message)

    def __str__(self):
        return f"Diff Parse Error: {self.message}"


class RateLimitError(AtomGitAPIError):
    """Exception raised when the AtomGit API rate limit is exhausted.

    Carries the ``x-ratelimit-*`` response headers described in the official
    API docs so callers can decide whether to back off or abort.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
        limit: int | None = None,
        remaining: int | None = None,
        used: int | None = None,
        reset: int | None = None,
    ):
        self.limit = limit
        self.remaining = remaining
        self.used = used
        self.reset = reset
        super().__init__(message, status_code=status_code, response_body=response_body)

    def __str__(self):
        base = super().__str__()
        details = []
        if self.remaining is not None:
            details.append(f"remaining={self.remaining}")
        if self.limit is not None:
            details.append(f"limit={self.limit}")
        if self.reset is not None:
            details.append(f"reset={self.reset}")
        if details:
            return f"{base} ({', '.join(details)})"
        return base


class URLError(AtomGitSDKError):
    """Exception raised for URL parsing errors"""

    def __init__(self, message: str, url: str | None = None):
        self.message = message
        self.url = url
        super().__init__(self.message)

    def __str__(self):
        if self.url:
            return f"URL Error: {self.message} (URL: {self.url})"
        return f"URL Error: {self.message}"
