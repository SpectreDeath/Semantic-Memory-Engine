import torch
import gc

def main():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("GTX 1660 Ti: VRAM Cache Flushed Successfully.")
    else:
        print("No CUDA device detected.")

if __name__ == "__main__":
    main()
