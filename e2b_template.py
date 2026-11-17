"""Build an E2B template with deps preinstalled and more RAM. Needs E2B_API_KEY in env."""
import sys
from e2b import Template
cpu = int(sys.argv[1]) if len(sys.argv) > 1 else 2
mem = int(sys.argv[2]) if len(sys.argv) > 2 else 4096
t = (Template().from_python_image("3.11")
     .apt_install(["ffmpeg"])
     .run_cmd("pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu av numpy opencv-python-headless pillow"))
b = Template.build(t, f"rvm-keying-{cpu}cpu", cpu_count=cpu, memory_mb=mem, on_build_logs=lambda l: print(str(l)[:120]))
print("built", b.name if hasattr(b, "name") else b)
