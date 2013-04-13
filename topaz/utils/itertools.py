def combinations(iterable, r):
    n = len(iterable)
    if r > n or r < 0:
        return
    assert r >= 0
    pool = list(iterable)
    indices = range(r)
    yield [pool[i] for i in indices]
    while True:
        for i in range(r - 1, -1, -1):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i + 1, r):
            indices[j] = indices[j - 1] + 1
        yield [pool[i] for i in indices]

def combinations_with_replacement(iterable, r):
    n = len(iterable)
    if r < 0:
        return
    assert r >= 0
    pool = list(iterable)
    indices = [0] * r
    yield [pool[i] for i in indices]
    while True:
        for i in range(r - 1, -1, -1):
            if indices[i] != n - 1:
                break
        else:
            return
        ii = indices[i]
        del indices[i:]
        indices.extend([ii + 1] * (r - i))
        yield [pool[i] for i in indices]

def permutations(iterable, r):
    n = len(iterable)
    if r > n or r < 0:
        return
    assert r >= 0
    pool = list(iterable)
    indices = range(n)
    cycles = range(n, n - r, -1)
    yield [pool[i] for i in indices[:r]]
    while n:
        for i in range(r - 1, -1, -1):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices.append(indices.pop(i))
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield [pool[i] for i in indices[:r]]
                break
        else:
            return

