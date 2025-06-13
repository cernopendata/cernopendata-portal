import React from 'react';
import { safeParse } from "../utils";

const RangeSlider = ({ min, max, value, onChange }) => {
  const rangeMin = safeParse(min, 1900);
  const rangeMax = safeParse(max, 2025);
  const step = 1;

  const [currentMinInputVal, currentMaxInputVal] = value;
  const minVal = Math.min(currentMinInputVal, currentMaxInputVal);
  const maxVal = Math.max(currentMinInputVal, currentMaxInputVal);

  const getPercent = (v) => {
    if (rangeMax === rangeMin) return 0;
    const percentage = ((v - rangeMin) / (rangeMax - rangeMin)) * 100;
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
        min={rangeMin}
        max={rangeMax}
        step={step}
        value={currentMinInputVal}
        onChange={handleMinChange}
        className="thumb thumb-left"
      />
      <input
        type="range"
        min={rangeMin}
        max={rangeMax}
        step={step}
        value={currentMaxInputVal}
        onChange={handleMaxChange}
        className="thumb thumb-right"
      />
      <div
        className={`slider-label ${areLabelsClose ? 'diagonal' : ''}`}
        style={{
          left: `${minLabelPlacement()}%`,
        }}
      >
        {minVal}
      </div>
      <div
        className={`slider-label ${areLabelsClose ? 'diagonal' : ''}`}
        style={{
          left: `${maxLabelPlacement()}%`,
          visibility: minVal === maxVal ? 'hidden' : ''
        }}
      >
        {maxVal}
      </div>
    </div>
  );
};

export default RangeSlider;