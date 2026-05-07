export function useFormatToQueryParams(data) {
  const queryParams = [];

  for (const key in data) {
    if (data[key] !== undefined && data[key] !== null && data[key] !== "") {
      if (Array.isArray(data[key])) {
        queryParams.push(`${key}=${data[key].join(",")}`);
      } else {
        queryParams.push(`${key}=${encodeURIComponent(data[key])}`);
      }
    }
  }

  return queryParams.join("&");
}
