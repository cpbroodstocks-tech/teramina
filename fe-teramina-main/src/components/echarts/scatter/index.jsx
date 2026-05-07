import { Fragment } from "react";
import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { ScatterChart, LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  DatasetComponent,
  LegendComponent,
  TitleComponent,
  VisualMapComponent,
} from "echarts/components";
import { SVGRenderer } from "echarts/renderers";

const ScatterCharts = ({ option = {}, inlineStyle = {}, className = "" }) => {
  echarts.use([
    TooltipComponent,
    GridComponent,
    ScatterChart,
    LineChart,
    SVGRenderer,
    DatasetComponent,
    LegendComponent,
    TitleComponent,
    VisualMapComponent,
  ]);

  return (
    <Fragment>
      <ReactEChartsCore
        echarts={echarts}
        notMerge={true}
        lazyUpdate={true}
        option={option}
        className={className}
        style={{
          height: "300px",
          width: "100%",
          ...inlineStyle,
        }}
      />
    </Fragment>
  );
};

export default ScatterCharts;
