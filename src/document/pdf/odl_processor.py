import tempfile
from pathlib import Path
from typing import Optional

import opendataloader_pdf
from ray import serve


@serve.deployment(ray_actor_options={"num_cpus": 0.5})
class PDFProcessorODL:
    def __init__(self):
        pass

    def __call__(self, file: Path) -> Optional[str]:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                opendataloader_pdf.convert(
                    input_path=[str(file)],
                    output_dir=temp_dir,
                    format="html"
                )
                output_file = Path(temp_dir) / f"{file.stem}.html"
                return output_file.read_text(encoding="utf-8")
        except:
            return None
