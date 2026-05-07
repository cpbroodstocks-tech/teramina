const useNDayAfter = (date, n) => {
  const result = new Date(date);
  result.setDate(result.getDate() + n)

  return result;
}

export { useNDayAfter }