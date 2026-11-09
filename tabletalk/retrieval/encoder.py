"""Quantized MiniLM: local sentence embeddings, no generation or remote inference."""
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from tabletalk.catalog import DATA
from tabletalk.retrieval.words import semantic_text


class Encoder:
    def __init__(self):
        path = DATA / "encoder"
        self.tokenizer = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=256)
        self.tokenizer.enable_padding()
        ort.disable_telemetry_events()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        self.session = ort.InferenceSession(str(path / "model.onnx"), options,
                                            providers=["CPUExecutionProvider"])

    def encode(self, texts):
        batches = []
        for start in range(0, len(texts), 16):
            batch = self.tokenizer.encode_batch([semantic_text(t) for t in texts[start:start + 16]])
            ids = np.asarray([t.ids for t in batch], dtype=np.int64)
            mask = np.asarray([t.attention_mask for t in batch], dtype=np.int64)
            tokens, = self.session.run(None, {"input_ids": ids, "attention_mask": mask,
                                               "token_type_ids": np.zeros_like(ids)})
            pooled = (tokens * mask[:, :, None]).sum(1) / mask.sum(1, keepdims=True)
            batches.append(pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-9))
        return np.vstack(batches).astype(np.float32)
