import math, random, sys, hashlib

class ElasticHashTableSHA256: 
    def __init__(self, capacity, delta=0.1, random_seed=None): 
        self.random_gen = random.Random(random_seed)
        if capacity <= 0:
            raise ValueError("Capacity must be positive.")
        if not (0 < delta < 1):
            raise ValueError("delta must be between 0 and 1.")
        self.capacity = capacity
        self.delta = delta
        self.max_inserts = capacity - int(delta * capacity)
        self.num_inserts = 0

        num_levels = max(1, math.floor(math.log2(capacity)))
        sizes = []
        total_assigned = 0

        for i in range(num_levels - 1):
            size = max(1, capacity // (2 ** (i + 1)))
            sizes.append(size)
            total_assigned += size

        sizes.append(capacity - total_assigned)
        self.levels = [[None] * s for s in sizes]
        self.salts = [self.random_gen.randint(0, sys.maxsize) for _ in range(num_levels)]
        self.occupancies = [0] * num_levels
        self.c = 4
        self.probes = 0

    def _hash(self, key, level):
        key_bytes = str(key).encode()
        salt_bytes = str(self.salts[level]).encode()
        h = hashlib.sha256(key_bytes + salt_bytes).digest()
        return int.from_bytes(h[:4], 'big')

    def _quad_probe(self, key, level, j, table_size): 
        return (self._hash(key, level) + j * j) % table_size

    def insert(self, key, value):
        self.probes = 0
        if self.num_inserts >= self.max_inserts:
            raise RuntimeError("Hash table is full (maximum allowed insertions reached).")
        for i, level in enumerate(self.levels):
            size = len(level)
            occ = self.occupancies[i]
            free = size - occ
            load = free / size
            probe_limit = int(max(1, self.c * min(
                math.log2(1 / load) if load > 0 else 0,
                math.log2(1 / self.delta),
            )))
            if i < len(self.levels) - 1:
                next_level = self.levels[i + 1]
                next_occ = self.occupancies[i + 1]
                next_free = len(next_level) - next_occ
                load_next = (next_free / len(next_level)) if len(next_level) > 0 else 0
                threshold = 0.25
                if load > (self.delta / 2) and load_next > threshold:
                    for j in range(probe_limit):
                        idx = self._quad_probe(key, i, j, size)
                        self.probes += 1
                        if level[idx] is None:
                            level[idx] = (key, value)
                            self.occupancies[i] += 1
                            self.num_inserts += 1
                            return True
                        elif level[idx][0] == key:
                            level[idx] = (key, value)
                            return True
                elif load <= (self.delta / 2):
                    continue
                elif load_next <= threshold:
                    for j in range(size):
                        idx = self._quad_probe(key, i, j, size)
                        self.probes += 1
                        if level[idx] is None:
                            level[idx] = (key, value)
                            self.occupancies[i] += 1
                            self.num_inserts += 1
                            return True 
                        elif level[idx][0] == key:
                            level[idx] = (key, value)
                            return True
            else:
                for j in range(size):
                    idx = self._quad_probe(key, i, j, size)
                    self.probes += 1
                    if level[idx] is None:
                        level[idx] = (key, value)
                        self.occupancies[i] += 1
                        self.num_inserts += 1
                        return True
                    elif level[idx][0] == key:
                        level[idx] = (key, value)
                        return True
        raise RuntimeError("Insertion failed in all levels; hash table is full.")

    def search(self, key):
        for i, level in enumerate(self.levels):
            size = len(level)
            for j in range(size):
                idx = self._quad_probe(key, i, j, size)
                entry = level[idx]
                if entry is None:
                    break
                if entry[0] == key:
                    return entry[1]
        return None
    
    def __setitem__(self, key, value):
        self.insert(key, value)

    def __getitem__(self, key):
        ret = self.search(key)
        if ret is None:
            raise KeyError(key)
        return ret

    def get(self, key, default=None):
        return self.search(key) or default

    def __contains__(self, key):
        return self.search(key) is not None

    def __len__(self):
        return self.num_inserts

