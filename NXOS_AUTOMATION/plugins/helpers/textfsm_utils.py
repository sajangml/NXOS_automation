import os
import textfsm
from io import StringIO

def parse_with_textfsm(platform: str, command: str, raw_output: str):
    """
    Parses device output using ntc-templates TextFSM library.
    Template path auto-discovers from installed ntc-templates.
    """
    template_dir = os.environ.get("NTC_TEMPLATES_DIR", "")
    if not template_dir:
        # Auto-locate from installed ntc_templates
        import ntc_templates
        template_dir = ntc_templates.__path__[0]

    template_path = os.path.join(template_dir, "templates")
    index_file = os.path.join(template_path, "index")

    with open(index_file, "r") as idx:
        for line in idx:
            if platform in line and command in line:
                tmpl_file = line.strip().split(",")[-1].strip()
                tmpl_path = os.path.join(template_path, tmpl_file)
                with open(tmpl_path, "r") as tmpl:
                    fsm = textfsm.TextFSM(tmpl)
                    parsed = fsm.ParseText(raw_output)
                    return [dict(zip(fsm.header, row)) for row in parsed]
    return []
