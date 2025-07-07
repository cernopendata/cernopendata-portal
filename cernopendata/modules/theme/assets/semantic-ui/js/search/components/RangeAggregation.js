import _debounce from 'lodash/debounce';
import PropTypes from "prop-types";
import React, { useState, useMemo, useEffect, useRef, useCallback } from "react";
import { useSelector } from "react-redux";
import { FlexibleWidthXYPlot, VerticalRectSeries, Hint } from "react-vis";
import { Card } from "semantic-ui-react";
import RangeSlider from './RangeSlider';
import { withState } from 'react-searchkit';

const HALF_BAR_WIDTH = 0.4;
const SELECTED_COLOR = "#91d5ff";
const DESELECTED_COLOR = "#bfbfbf";
const HIGHLIGHT_COLOR = "#69c0ff";


function extractBuckets(resultsAggregations, key) {
    if (resultsAggregations && resultsAggregations[key] && Array.isArray(resultsAggregations[key].buckets)) {
        return resultsAggregations[key].buckets;
    }
    return [];
}

function getInitialHistogramData(initialBuckets) {
  const data = initialBuckets.map(item => {
    const key = Number(item.key_as_string);
    return {
      x0: key - HALF_BAR_WIDTH,
      x: key + HALF_BAR_WIDTH,
      y: item.doc_count,
      color: DESELECTED_COLOR,
    };
  });
  return data;
}

function getHistogramData(initialData, [lower, upper]) {
  const data = initialData.map((item, index) => {
    const { x0, x, y } = item;
    const bucketKey = x - HALF_BAR_WIDTH;
    const color = (bucketKey >= lower && bucketKey <= upper)
      ? SELECTED_COLOR
      : DESELECTED_COLOR;
    return {
      x0,
      x,
      y,
      index,
      color,
    };
  });
  return data;
}

const RangeAggregation = (props) => {
  const { title, agg, currentQueryState } = props;
  const resultsAggregations = useSelector(
    (state) => state.results.data.aggregations
  );
  const initialBuckets = extractBuckets(resultsAggregations, agg.aggName)
  const keys = initialBuckets.map(bucket => Number(bucket.key_as_string));
  const min = Math.min(...keys);
  const max = Math.max(...keys);
  const [range, setRange] = useState([min, max]);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [hoveredBar, setHoveredBar] = useState(null);

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
    if (Number.isFinite(min) && Number.isFinite(max) && range[0] === undefined && range[1] === undefined) {
      setRange([min, max]);
    }
  }, [min, max]);

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
    ({ x }) => {
      const bucketKey = x - HALF_BAR_WIDTH;
      const endpoints = [bucketKey, bucketKey];
      onSliderChange(endpoints);
    },
    [onSliderChange]
  );

  const handleValueMouseOver = useCallback((datapoint) => {
    setHoveredIndex(datapoint.index);
    setHoveredBar(datapoint);
  }, []);

  const handleValueMouseOut = useCallback(() => {
    setHoveredIndex(null);
    setHoveredBar(null);
  }, []);

  const bars = data.map((item, i) => ({
    ...item,
    color: i === hoveredIndex ? HIGHLIGHT_COLOR : item.color,
  }));

  if (!initialData.length) {
    return (<></>)
  }

  return (
    <Card>
      <Card.Content>
        <Card.Header>{title}</Card.Header>
      </Card.Content>
      <Card.Content>
        <FlexibleWidthXYPlot height={100} margin={0}>
          <VerticalRectSeries
            colorType="literal"
            data={initialData}
            onValueClick={onBarClick}
            onValueMouseOver={handleValueMouseOver}
            onValueMouseOut={handleValueMouseOut}
          />
          {hoveredBar && (
            <Hint
              value={hoveredBar}
              align={{ vertical: 'bottom', horizontal: 'auto' }}
              format={({ x, y }) => {
                return [
                  { title: 'Results', value: y },
                  { title: title, value: x - 0.4 },
                ];
              }}
            />
          )}
          <VerticalRectSeries
            colorType="literal"
            data={bars}
            onValueClick={onBarClick}
            onValueMouseOver={handleValueMouseOver}
            onValueMouseOut={handleValueMouseOut}
          />
        </FlexibleWidthXYPlot>
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
