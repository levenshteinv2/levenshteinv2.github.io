function boundedDistance(x, y, k) {
    // x and y are arrays of sequence elements; k is a nonnegative integer.
    if (!Number.isSafeInteger(k) || k < 0 || k >= Number.MAX_SAFE_INTEGER)
        throw new RangeError("Invalid threshold");
    if (Math.abs(x.length - y.length) > k) return k + 1;
    const inf = k + 1;
    let prev = new Map();
    for (let j = 0; j <= Math.min(y.length, k); j++) prev.set(j, j);
    for (let i = 1; i <= x.length; i++) {
        const cur = new Map();
        for (let j = Math.max(0, i-k); j <= Math.min(y.length, i+k); j++) {
            const value = j === 0 ? i : Math.min(inf,
                (prev.get(j) ?? inf) + 1,
                (cur.get(j-1) ?? inf) + 1,
                (prev.get(j-1) ?? inf) + Number(x[i-1] !== y[j-1]));
            cur.set(j, value);
        }
        prev = cur;
    }
    return prev.get(y.length) ?? inf;
}
export { boundedDistance };
