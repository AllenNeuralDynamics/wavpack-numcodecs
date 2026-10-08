from zarr.abc.codec import ArrayBytesCodec
from zarr.core.buffer import Buffer, BufferPrototype
from zarr.core.common import BytesLike
from wavpack_numcodecs.wavpack import WavPack as WavPackV2
import numpy as np
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zarr.core.array_spec import ArraySpec


class WavPack(ArrayBytesCodec):
    codec_id = "wavpack"

    def __init__(
        self,
        level: int = 1,
        bps: int | None = None,
        dynamic_noise_shaping: bool = True,
        shaping_weight: float = 0.0,
        num_encoding_threads: int = 1,
        num_decoding_threads: int = 8,
    ):
        self._codec = WavPackV2(
            level=level,
            bps=bps,
            dynamic_noise_shaping=dynamic_noise_shaping,
            shaping_weight=shaping_weight,
            num_encoding_threads=num_encoding_threads,
            num_decoding_threads=num_decoding_threads,
        )

    async def _encode_single(
        self,
        chunk_array: np.ndarray,
        chunk_spec: "ArraySpec",
    ) -> Buffer | None:
        """Encode a single chunk."""
        # Convert to numpy array if it's an NDBuffer
        if hasattr(chunk_array, "as_numpy_array"):
            chunk_array = chunk_array.as_numpy_array()
        elif not isinstance(chunk_array, np.ndarray):
            chunk_array = np.asarray(chunk_array)

        if not chunk_array.data.contiguous:
            chunk_array = np.ascontiguousarray(chunk_array)

        encoded = await asyncio.to_thread(self._codec.encode, chunk_array)
        return chunk_spec.prototype.buffer.from_bytes(encoded)

    async def _decode_single(
        self,
        chunk_bytes: Buffer,
        chunk_spec: "ArraySpec",
    ) -> np.ndarray:
        """Decode a single chunk."""
        decoded = await asyncio.to_thread(self._codec.decode, chunk_bytes.to_bytes())

        # Convert to numpy array if it's bytes
        if isinstance(decoded, bytes):
            np_dtype = chunk_spec.dtype.to_native_dtype()
            decoded = np.frombuffer(decoded, dtype=np_dtype)

        # Ensure it's a numpy array with correct shape
        if isinstance(decoded, np.ndarray):
            return decoded.reshape(chunk_spec.shape)
        else:
            raise TypeError(f"Expected numpy array from decode, got {type(decoded)}")

    def compute_encoded_size(self, input_byte_length: int, chunk_spec: "ArraySpec") -> int:
        # WavPack compression ratio is variable, so we can't predict the exact size
        # Return a conservative estimate
        return input_byte_length

    def to_dict(self) -> dict:
        """Serialize to zarr v3 codec metadata (uses 'name' key)."""
        config = self._codec.get_config()
        return {
            "name": self.codec_id,
            "level": config["level"],
            "bps": config["bps"] if config["bps"] else None,
            "dynamic_noise_shaping": config["dynamic_noise_shaping"],
            "shaping_weight": config["shaping_weight"],
            "num_encoding_threads": config["num_encoding_threads"],
            "num_decoding_threads": config["num_decoding_threads"],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WavPack":
        """Reconstruct from zarr v3 codec metadata."""
        data = {k: v for k, v in data.items() if k != "name"}
        return cls(**data)
