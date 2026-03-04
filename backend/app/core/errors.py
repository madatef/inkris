from app.core.error_registry import ErrorContract


class AppError(Exception):
    def __init__(self, specs: ErrorContract):
        self.code = specs.code
        self.message = specs.message
        self.status_code = specs.status_code
        self.field = specs.field
        super().__init__(specs.message)

    