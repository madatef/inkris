from app.core.enums import FileExtensionEnum


EXTENSION_TO_MIME = {
    FileExtensionEnum.PDF: "application/pdf",
    FileExtensionEnum.TXT: "text/plain",
    FileExtensionEnum.MD: "text/markdown",
    FileExtensionEnum.XLS: "application/vnd.ms-excel",
    FileExtensionEnum.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
