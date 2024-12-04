import React, {useState} from "react";
import ReactDOM from "react-dom";

import Confetti from 'react-confetti'


const unlock_date = new Date("2024-12-09")

function Celebrate() {
    const [stateShowConfetti, setShowConfetti] = useState(false);
    // const [stateShowBlog, setShowBlog] = useState(false);

    let make_confetti = () => {
        if (stateShowConfetti) return;

        setShowConfetti(true);
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
                    setShowConfetti(false);
                }}
            />,
            confettiContainer
        )
    }

    return (
        <div className="navbar-anniversary-wrap" title="Click the cake to celebrate!">
            <button onClick={make_confetti} disabled={stateShowConfetti}>
                {!stateShowConfetti ? "🎂" : "🎉"}
            </button>
            <a className="navbar-anniversary-texts" href="/docs/ten-years-of-cern-open-data-portal">
                <span className="navbar-anniversary-texts-title">
                    <strong>Ten years</strong> of CERN Open Data portal!
                </span><br/>
                <span className="navbar-anniversary-texts-subtitle">
                    (anniversary blog)
                </span>
            </a>
            <div id="confetti-holder"></div>
        </div>
    )
}

if (new Date() > unlock_date) {
    const titleContainer = document.getElementById("react-anniversary")
    ReactDOM.render(React.createElement(Celebrate), titleContainer)
}
