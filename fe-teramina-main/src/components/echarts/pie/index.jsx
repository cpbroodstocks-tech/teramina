import { Fragment } from "react";
import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { PieChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  DatasetComponent,
  TitleComponent,
} from "echarts/components";
import { SVGRenderer } from "echarts/renderers";

const PieEcharts = ({ option = {}, inlineStyle = {}, className = "" }) => {
  echarts.use([
    TitleComponent,
    TooltipComponent,
    GridComponent,
    PieChart,
    SVGRenderer,
    DatasetComponent,
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
          height: "350px",
          width: "100%",
          ...inlineStyle,
        }}
      />
    </Fragment>
  );
};

export default PieEcharts;
