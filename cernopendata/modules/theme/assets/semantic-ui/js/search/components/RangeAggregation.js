import _debounce from 'lodash/debounce';
import PropTypes from "prop-types";
import React, { useState, useMemo, useEffect, useRef, useCallback } from "react";
import { useSelector } from "react-redux";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import { Card } from "semantic-ui-react";
import RangeSlider from './RangeSlider';
import { withState } from 'react-searchkit';

const SELECTED_COLOR = "#91d5ff";
const DESELECTED_COLOR = "#bfbfbf";
const HIGHLIGHT_COLOR = "#69c0ff";


function extractBuckets(resultsAggregations, key) {
    if (resultsAggregations && resultsAggregations[key] && Array.isArray(resultsAggregations[key].buckets)) {
        return resultsAggregations[key].buckets;
    }
    return [];
}

function getInitialHistogramData(initialBuckets, min, max) {
  const dataMap = new Map();

  initialBuckets.forEach(item => {
    const key = Number(item.key_as_string);
    dataMap.set(key, {
      name: key,
      y: item.doc_count,
      color: DESELECTED_COLOR
    });
  });

  const completeData = [];
  for (let year = min; year <= max; year++) {
    if (dataMap.has(year)) {
      completeData.push(dataMap.get(year));
    } else {
      completeData.push({
        name: year,
        y: 0,
        color: DESELECTED_COLOR
      });
    }
  }

  return completeData;
}

function getHistogramData(initialData, [lower, upper]) {
  return initialData.map((item, index) => {
    const { name } = item;
    const color = (name >= lower && name <= upper) ?
      SELECTED_COLOR :
      DESELECTED_COLOR;

    return {
      ...item,
      color,
      index,
    };
  });
}

const CustomTooltip = ({ active, payload, label, title }) => {
  if (active && payload && payload.length) {
    const dataPoint = payload[0].payload;
    if (dataPoint.y) {
      return (
        <div className="range-tooltip">
          <p style={{ margin: 0 }}><strong>Results:</strong> {dataPoint.y}</p>
          <p style={{ margin: 0 }}><strong>{title}:</strong> {dataPoint.name}</p>
        </div>
      );
    }
  }
  return null;
};

const RangeAggregation = (props) => {
  const { title, agg, currentQueryState } = props;
  const resultsAggregations = useSelector(
    (state) => state.results.data.aggregations
  );
  const initialBuckets = extractBuckets(resultsAggregations, agg.aggName);
  const keys = initialBuckets.map(bucket => Number(bucket.key_as_string));
  const min = keys.length ? Math.min(...keys) : 0;
  const max = keys.length ? Math.max(...keys) : 0;

  const [range, setRange] = useState([min, max]);
  const [hoveredData, setHoveredData] = useState(null);

  useEffect(() => {
    const currentFilter = currentQueryState.filters.find(
      (filter) => Array.isArray(filter) && filter[0] === agg.aggName
    );
    if (!currentFilter) {
      setRange([min, max]);
    } else {
      let [from, to] = currentFilter[1].split("--").map(Number);
      from = from < min ? min : from;
      to = to > max ? max : to;
      if (range[0] !== from || range[1] !== to) {
        setRange([from, to]);
      }
    }
  }, [currentQueryState.filters, agg.aggName, min, max]);

  useEffect(() => {
    if (Number.isFinite(min) && Number.isFinite(max) && (range[0] === undefined || range[1] === undefined)) {
      setRange([min, max]);
    }
  }, [min, max, range]);

  const initialData = useMemo(
    () => getInitialHistogramData(initialBuckets, min, max),
    [initialBuckets, min, max]
  );
  const data = useMemo(
    () => getHistogramData(initialData, range),
    [initialData, range]
  );

  const updateQuery = useRef(
    _debounce((newRange, queryState) => {
      newRange.sort();
      const [from, to] = newRange;
      const newFilterValue = `${from}--${to}`;
      const currentFilters = (queryState.filters || []).filter(
        (filter) => Array.isArray(filter) && filter[0] !== agg.aggName
      );
      props.updateQueryState({
        ...queryState,
        filters: [...currentFilters, [agg.aggName, newFilterValue]],
      });
    }, 500)
  ).current;

  function onSliderChange(newRange) {
    setRange(newRange);
    updateQuery(newRange, props.currentQueryState);
  }

  const onBarClick = useCallback(
    (dataPoint) => {
      const bucketKey = dataPoint.name;
      const endpoints = [bucketKey, bucketKey];
      onSliderChange(endpoints);
    },
    [onSliderChange]
  );

  const handleBarMouseOver = useCallback((data) => {
    setHoveredData(data);
  }, []);

  const handleBarMouseOut = useCallback(() => {
    setHoveredData(null);
  }, []);

  if (!initialData.length) {
    return (<></>)
  }

  return (
    <Card>
      <Card.Content>
        <Card.Header>{title}</Card.Header>
      </Card.Content>
      <Card.Content>
        <ResponsiveContainer width="100%" height={100}>
          <BarChart
            data={data}
          >
            <XAxis dataKey="name" hide />
            <YAxis hide />

            <Tooltip
              cursor={{ fill: 'transparent' }}
              content={<CustomTooltip title={title} />}
            />

            <Bar
              dataKey="y"
              onClick={onBarClick}
              onMouseOver={handleBarMouseOver}
              onMouseOut={handleBarMouseOut}
            >
              {
                data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={hoveredData && hoveredData.index === index ? HIGHLIGHT_COLOR : entry.color}
                  />
                ))
              }
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div style={{ margin: "1em 0" }}>
          <RangeSlider
            min={min}
            max={max}
            value={range}
            onChange={onSliderChange}
          />
        </div>
      </Card.Content>
    </Card>
  );
};


RangeAggregation.propTypes = {
  title: PropTypes.string.isRequired,
  agg: PropTypes.shape({
    field: PropTypes.string.isRequired,
    aggName: PropTypes.string.isRequired,
    childAgg: PropTypes.object,
  }).isRequired,
};

export default withState(RangeAggregation);
