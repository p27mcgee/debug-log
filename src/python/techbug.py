from src.python.debuglog.buggin import generate_filtered_logs
from src.python.debuglog.buggin import NOT

TECH = "tech"
NOAPP = "noapp"
NOPUT = "noput"
ADD = "add"
PWACL = "parrwebappcl"
PLATCL = "platcl"
signature_map = {
    TECH: " TechnologyClassListener]",
    NOAPP: " - Couldn't find app for ",
    NOPUT: " - Not putting ",
    ADD: " - Adding ",
    PWACL: r"/ParallelWebappClassLoader",
    PLATCL: r"/jdk.internal.loader.ClassLoaders$PlatformClassLoader@"
}

signature_names = [
        [TECH],
        [TECH, NOAPP],
        [TECH, NOAPP, PLATCL],
        [TECH, NOAPP, NOT, PLATCL, PWACL],
        [TECH, NOAPP, NOT, PLATCL, NOT, PWACL],
        [TECH, NOT, NOAPP],
        [TECH, NOPUT],
        [TECH, ADD]
]

generate_filtered_logs(logs_signature_names=signature_names, debug_log="data/petclinic.log", output_dir="results",
            log_ext=".log", signature_map=signature_map)

