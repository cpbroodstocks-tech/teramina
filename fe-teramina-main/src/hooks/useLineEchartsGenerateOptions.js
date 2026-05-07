const getGridTopValue = (title, legend) => {
  if (title && (legend && ((legend.data && legend.data.length > 0) && legend.show))) {
    return "25%";
  } else if (title && (legend && ((legend.data && legend.data.length === 0) || !legend.show))) {
    return "17.5%";
  }
  return "5%";
}

const useLineEchartsGenerateOptions = () => ({
  generateOptionsScatterOverview: (title, options) => {
    const finalOptions = {
      ...options,
      title: {
        text: title,
        textStyle: {
          fontSize: "14px",
        },
      },
      textStyle: {
        fontFamily: "Lato",
        color: "#4F4F4F",
      },
      grid: {
        left: "2%",
        right: "2%",
        bottom: "2%",
        containLabel: true
      },
      tooltip: {
        trigger: "axis"
      },
    }
    return finalOptions;
  },

  generateOptionsKualitasAir: (title, options) => {
    const finalOptions = {
      ...options,
      title: {
        show: false,
        text: title,
        textStyle: {
          fontSize: "18px",
        },
      },
      legend: {
        ...options.legend,
        top: "12.5%",
      },
      textStyle: {
        fontFamily: "Lato",
        color: "#4F4F4F",
      },
      grid: {
        left: "1%",
        bottom: "0",
        top: getGridTopValue(title, options.legend),
        containLabel: true
      },
      tooltip: {
        trigger: "axis"
      },
      xAxis: {
        ...options.xAxis,
        type: "category",
        data: [...options.xAxis.data],
        splitLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLine: {
          show: false,
          lineStyle: {
            color: "#4F4F4F",
            width: 0.5,
          },
        },
      },
      yAxis: {
        ...options.yAxis,
        type: "value",
        splitLine: {
          show: true,
          lineStyle: {
            type: "dashed",
            color: "#C9CBCD",
          },
        },
        axisLine: {
          type: "dashed",
          show: false,
          lineStyle: {
            color: "#4F4F4F",
            width: 0.5,
          },
        },
        axisLabel: {
          fontWeight: 700,
          formatter: (value) => {
            return value;
          }
        },
      },
    }
    return finalOptions;
  },
  generateOptionsDefault: (title, options) => {
    const finalOptions = {
      ...options,
      title: {
        text: title,
        textStyle: {
          fontSize: "14px",
        },
      },
      legend: {
        ...options.legend,
        top: "12.5%",
      },
      textStyle: {
        fontFamily: "Lato",
        color: "#4F4F4F",
      },
      grid: {
        left: "2%",
        right: "2%",
        bottom: "2%",
        top: getGridTopValue(title, options.legend),
        containLabel: true
      },
      tooltip: {
        trigger: "axis"
      },
      xAxis: {
        type: "category",
        data: [...options.xAxis.data],
        splitLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: "#4F4F4F",
            width: 0.5,
          },
        },
      },
      yAxis: {
        type: "value",
        splitLine: {
          show: false,
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: "#4F4F4F",
            width: 0.5,
          },
        },
        axisLabel: {
          fontWeight: 700,
          formatter: (value) => {
            return value;
          }
        },
      },
    }
    return finalOptions;
  },
  generateOptionsWithMoneyFormatYAxis: (title, options) => {
    const finalOptions = {
      ...options,
      title: {
        text: title,
        textStyle: {
          fontSize: "14px",
        },
      },
      legend: {
        ...options.legend,
        top: "12.5%",
      },
      textStyle: {
        fontFamily: "Lato",
        color: "#4F4F4F",
      },
      grid: {
        left: "2%",
        right: "2%",
        bottom: "2%",
        top: getGridTopValue(title, options.legend),
        containLabel: true
      },
      tooltip: {
        trigger: "axis"
      },
      xAxis: {
        type: "category",
        data: [...options.xAxis.data],
        splitLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: "#4F4F4F",
            width: 0.5,
          },
        },
      },
      yAxis: {
        type: "value",
        splitLine: {
          show: false,
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: "#4F4F4F",
            width: 0.5,
          },
        },
        axisLabel: {
          fontWeight: 700,
          formatter: (value) => {
            if (parseFloat(value) >= 1000000) {
              return parseFloat(value) / 1000000 + "M";
            }

            if (parseFloat(value) >= 1000) {
              return parseFloat(value) / 1000 + "K";
            }

            return value;
          }
        },
      },
    }
    return finalOptions;
  },
})

export { useLineEchartsGenerateOptions }