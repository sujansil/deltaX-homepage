/* A link is navigation only; this does not start a round or check its health. */
function roundDestination(value, base) {
  if (typeof value !== 'string' || !value.trim()) return null;
  try {
    const url = new URL(value.trim(), base);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return null;
    return url.href;
  } catch { return null; }
}
for (const id of ['r1', 'r2']) {
  const url = roundDestination(window.ROUND_LINKS?.[id], window.location.href);
  if (url) {
    document.getElementById(id).href = url;
    document.getElementById(id).hidden = false;
    document.getElementById(`${id}-status`).hidden = true;
  }
}
