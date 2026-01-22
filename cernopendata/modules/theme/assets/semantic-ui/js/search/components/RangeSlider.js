import React from 'react';

const RangeSlider = ({ min, max, value, onChange }) => {
  const step = 1;

  const [currentMinInputVal, currentMaxInputVal] = value;
  const minVal = Math.min(currentMinInputVal, currentMaxInputVal);
  const maxVal = Math.max(currentMinInputVal, currentMaxInputVal);

  const getPercent = (v) => {
    if (max === min) return 0;
    const percentage = ((v - min) / (max - min)) * 100;
    return Math.min(Math.max(percentage, 0), 100);
  };

  const minPercent = getPercent(minVal);
  const maxPercent = getPercent(maxVal);

  const percentageDifference = maxPercent - minPercent;

  const areLabelsClose = percentageDifference < 20;
  const areLabelsOverlapping = percentageDifference < 10;

  const labelPlacement = (percentage) => {
    return percentage + ((- 3 * percentage)/50 + 3);
  };

  const labelOffset = () => {
    return (10 - percentageDifference) / 2;
  }

  const minLabelPlacement = () => {
    let placement = labelPlacement(minPercent)
    if (areLabelsOverlapping) {
      placement -= labelOffset()
    }
    return placement
  }

  const maxLabelPlacement = () => {
    let placement = labelPlacement(maxPercent)
    if (areLabelsOverlapping) {
      placement += labelOffset()
    }
    return placement
  }

  const handleMinChange = (e) => {
    onChange?.([Number(e.target.value), currentMaxInputVal]);
  };

  const handleMaxChange = (e) => {
    onChange?.([currentMinInputVal, Number(e.target.value)]);
  };

  return (
    <div className="slider-container">
      <div className="slider-track" />
      <div
        className="slider-range"
        style={{
          left: `${minPercent}%`,
          width: `${percentageDifference}%`,
        }}
      />
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={currentMinInputVal}
        onChange={handleMinChange}
        className="thumb thumb-left"
        aria-labelledby="min-label"
      />
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={currentMaxInputVal}
        onChange={handleMaxChange}
        className="thumb thumb-right"
        aria-labelledby="max-label"
      />
      <div
        id="min-label"
        className={`slider-label ${areLabelsClose ? "diagonal" : ""}`}
        style={{
          left: `${minLabelPlacement()}%`,
        }}
      >
        {minVal}
      </div>
      <div
        id="max-label"
        className={`slider-label ${areLabelsClose ? "diagonal" : ""}`}
        style={{
          left: `${maxLabelPlacement()}%`,
          visibility: minVal === maxVal ? "hidden" : "",
        }}
      >
        {maxVal}
      </div>
    </div>
  );
};

export default RangeSlider;