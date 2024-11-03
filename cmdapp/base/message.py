from ..render import Template

PATTERNS = {
    "action": "[ on {action}][ {what}][ within {scope}][ with {argument}][ = {value}][ because {reason}][: |result]^[{result}]",
    "argument": "[ The argument][ \[{argument}\]][ is {status}][ because {reason}][. {result}][. {recommend}]",
    "found": "/b[NOT |negative][FOUND][ {count}][/{total}][ {what}][ with {field}][: {items}]",
    "exception": "/*R[ERROR][ \[{type}\]][: |message]*Y['{message}']/*R[ on executing:\n|command]@C[{command}]@R[\n with |argument]@Y[{argument}]",
}

TEMPLATES = {
    "success": Template(f"/G[SUCCESS]{PATTERNS['action']}"),
    "error": Template(f"/*R[ERROR]{PATTERNS['action']}"),
    "argument_warning": Template(f"/Y[WARNING]{PATTERNS['argument']}"),
    "found_info": Template(PATTERNS["found"]),
    "exception": Template(PATTERNS["exception"]),
    "info": Template("/b[{0}]"),
    "custom": Template("[{0}]"),
}
