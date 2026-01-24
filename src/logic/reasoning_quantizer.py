import pandas as pd
import sqlite3
import numpy as np
import h5py
import os

class ReasoningQuantizer:
    """Distills ConceptNet into a lightweight, offline reasoning engine."""
    
    def __init__(self, db_path="data/knowledge_core.sqlite"):
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)

    def distill_assertions(self, csv_path):
        """Filters 30M+ rows into a high-weight English core."""
        print("🔍 Distilling Knowledge Graph...")
        # Reading in chunks to protect your 32GB RAM
        chunk_size = 100000
        try:
            for chunk in pd.read_csv(csv_path, sep='\t', names=['uri', 'rel', 'start', 'end', 'info'], chunksize=chunk_size):
                # Filter for English entries
                en_core = chunk[chunk['start'].str.startswith('/c/en/', na=False)]
                # Insert into SQLite
                en_core.to_sql('assertions', self.conn, if_exists='append', index=False)
            
            print("Indexing database for high-speed lookups...")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_start ON assertions(start)")
            print("✅ Distillation Complete.")
        except Exception as e:
            print(f"❌ Error during distillation: {e}")

    def quantize_vectors(self, h5_path, output_path="data/numberbatch_mini.npz"):
        """Compresses 300d vectors to 16-bit to save VRAM on the 1660 Ti."""
        print("📉 Quantizing Numberbatch Vectors...")
        try:
            with h5py.File(h5_path, 'r') as f:
                # Numberbatch HDF5 structure: mat/axis1 (labels) and mat/block0_values (vectors)
                labels = f['mat']['axis1'][:]
                vectors = f['mat']['block0_values'][:]
                
                # Cast to float16 - halves memory usage (approx 1GB vs 2GB)
                compressed_vecs = vectors.astype(np.float16)
                np.savez_compressed(output_path, labels=labels, vectors=compressed_vecs)
            print(f"✅ Quantized vectors saved to {output_path}")
        except Exception as e:
            print(f"❌ Error during quantization: {e}")

if __name__ == "__main__":
    # Initialize the Quantizer
    quantizer = ReasoningQuantizer()

    # PATHS - Ensure these files are unzipped and in the /data folder!
    CSV_INPUT = "data/conceptnet-assertions-5.7.0.csv"
    H5_INPUT = "data/numberbatch-en.h5"

    # Step 1: Distill the Knowledge Graph (CSV -> SQLite)
    if os.path.exists(CSV_INPUT):
        quantizer.distill_assertions(CSV_INPUT)
    else:
        print(f"⚠️ Missing {CSV_INPUT}. Skipping distillation.")

    # Step 2: Quantize the Vectors (H5 -> NPZ)
    if os.path.exists(H5_INPUT):
        quantizer.quantize_vectors(H5_INPUT)
    else:
        print(f"⚠️ Missing {H5_INPUT}. Skipping vector quantization.")
if __name__ == "__main__":
    # Initialize the Quantizer
    quantizer = ReasoningQuantizer()

    # FORCE ABSOLUTE PATHS for Windows
    # The 'r' prefix is critical for handling backslashes correctly
    CSV_INPUT = r"D:\mcp_servers\data\conceptnet-assertions-5.7.0.csv"
    H5_INPUT = r"D:\mcp_servers\data\numberbatch-en.h5"

    print(f"Checking for CSV at: {CSV_INPUT}")
    # Step 1: Distill the Knowledge Graph (CSV -> SQLite)
    if os.path.exists(CSV_INPUT):
        quantizer.distill_assertions(CSV_INPUT)
    else:
        print(f"⚠️ Still can't find CSV at {CSV_INPUT}")

    print(f"Checking for H5 at: {H5_INPUT}")
    # Step 2: Quantize the Vectors (H5 -> NPZ)
    if os.path.exists(H5_INPUT):
        quantizer.quantize_vectors(H5_INPUT)
    else:
        print(f"⚠️ Still can't find H5 at {H5_INPUT}")