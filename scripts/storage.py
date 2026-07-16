import numpy as np


def save_binary_matrix(path: str, mat: np.ndarray):
    assert mat.ndim == 2, "必须二维"
    h, w = mat.shape
    assert h == w, "必须方阵"
    assert h <= 255, "边长不能超过255"
    mat = mat.astype(np.bool_)
    packed = np.packbits(mat, axis=None)
    with open(path, "wb") as f:
        f.write(bytes([h]))
        f.write(packed.tobytes())

def load_binary_matrix(path: str):
    with open(path, "rb") as f:
        N = f.read(1)[0]
        packed = np.frombuffer(f.read(), dtype=np.uint8)
    bits = np.unpackbits(packed)
    return bits[:N * N].reshape((N, N)).astype(bool)

if __name__ == "__main__":
    A = np.random.randint(0, 2, (17, 17), dtype=np.uint8)
    save_binary_matrix("test.bin", A)
    B = load_binary_matrix("test.bin")
    print(np.array_equal(A.astype(bool), B))