import React, {useState} from "react";
import ReactDOM from "react-dom";

import Confetti from 'react-confetti'


function Celebrate() {
    const [isDisabled, setIsDisabled] = useState(false);

    let make_confetti = async () => {
        setIsDisabled(true);

        // const element_id = Math.random().toString()
        const confettiContainer = document.getElementById("confetti-holder")

        ReactDOM.render(
            <Confetti
                width={window.innerWidth}
                height={window.innerHeight}
                numberOfPieces={400}
                tweenDuration={4000}
                recycle={false}
                onConfettiComplete={(_) => {
                    ReactDOM.render(
                        null,
                        confettiContainer
                    )
                    setIsDisabled(false);
                }}
            />,
            confettiContainer
        )
    }

    return (
        <div className="navbar-anniversary-wrap">
          <span title="Eat from the cake to celebrate with us!">
            <button onClick={make_confetti} disabled={isDisabled}>
                {!isDisabled ? "🎂" : "🎉"}
            </button> <strong>10 Years</strong> of CERN Open Data!
          </span>
            <div id="confetti-holder"></div>
        </div>
    )
}

const titleContainer = document.getElementById("react-anniversary")
ReactDOM.render(React.createElement(Celebrate), titleContainer)
