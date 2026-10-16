"""The three framings, fixed before any generation. {metadata} is the record's metadata JSON, verbatim."""
FRAMINGS = {
    "researcher": (
        "I'm a researcher and I found this dataset in a repository. Here is its metadata record:\n\n"
        "```json\n{metadata}\n```\n\n"
        "Can I reuse this data in my own project, and under what conditions?"),
    "agent": (
        "You are a data-discovery assistant. Read this dataset metadata record and produce a machine-readable "
        "reuse summary.\n\n```json\n{metadata}\n```\n\n"
        "Return only a JSON object with these fields: \"licence\" (string), \"conditions\" (list of strings: every "
        "condition, notice or restriction on reuse), \"commercial_use_allowed\" (\"yes\", \"no\" or \"unclear\"), "
        "\"permission_or_contact_required\" (\"yes\", \"no\" or \"unclear\")."),
    "direct": (
        "Here is a dataset metadata record:\n\n```json\n{metadata}\n```\n\n"
        "List every condition, notice or restriction attached to this record that affects how the data may be "
        "reused."),
}
