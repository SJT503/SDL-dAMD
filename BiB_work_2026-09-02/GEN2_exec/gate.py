# Portable preflight/canary decorator shim for external reproduction outside local harness
def gate(_file=None):
    return True

def gpu_gate():
    return True

def canary_gate(fn, desc='canary'):
    return fn()

def retry_limit(_n=2):
    def _dec(fn):
        return fn
    return _dec
