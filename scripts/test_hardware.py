"""
Hardware Benchmark: Gemma 4 E4B on Intel Arc A380 (GPU.1) via OpenVINO GenAI
"""

import os
import sys
import time
try:
    import openvino_genai as ov_genai
    import openvino as ov
except ImportError:
    ov_genai = None
    ov = None

MODEL_DIR = os.path.expanduser(r"~\.cache\models\gemma-4-E4B-it-int4-ov")
DEVICE = "GPU.1"


def benchmark():
    core = ov.Core()
    dev_name = core.get_property(DEVICE, "FULL_DEVICE_NAME")
    print("=" * 60)
    print(f"Target Device: {DEVICE} -> {dev_name}")
    print(f"Model Directory: {MODEL_DIR}")
    print("=" * 60)

    print("[1/3] Initializing and compiling VLMPipeline on Intel Arc A380...")
    t0 = time.time()
    pipe = ov_genai.VLMPipeline(MODEL_DIR, DEVICE)
    compile_time = time.time() - t0
    print(f"[+] Model compiled in {compile_time:.2f} seconds.")

    print("\n[2/3] Preparing test prompt...")
    prompt = (
        "<start_of_turn>user\n"
        "You are the founding scribe of the EON society. "
        "State your prime directive in two sentences.<end_of_turn>\n"
        "<start_of_turn>model\n"
    )

    config = ov_genai.GenerationConfig()
    config.max_new_tokens = 64
    config.temperature = 0.7

    print("[3/3] Generating tokens on Intel Arc A380...")
    t1 = time.time()
    output = pipe.generate(prompt, generation_config=config)
    gen_time = time.time() - t1

    print("\n" + "=" * 60)
    print("Inference Result:")
    print(output)
    print("=" * 60)
    print(f"Generation Time: {gen_time:.2f} s")
    print(f"Estimated throughput: {64 / gen_time:.2f} tokens/sec")
    print("=" * 60)


if __name__ == "__main__":
    benchmark()
