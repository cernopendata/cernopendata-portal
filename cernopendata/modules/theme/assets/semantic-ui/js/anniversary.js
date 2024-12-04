import React, {useState} from "react";
import ReactDOM from "react-dom";

import Confetti from 'react-confetti'


const unlock_date = new Date("2024-12-09")

function Celebrate() {
    const [stateShowConfetti, setShowConfetti] = useState(false);
    const [stateShowBlog, setShowBlog] = useState(false);

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
        <div
            className="navbar-anniversary-wrap"
            onMouseEnter={() => {
                setShowBlog(true)
            }}
            onMouseMove={() => {
                make_confetti()
            }}
            onMouseLeave={() => {
                setShowBlog(false)
            }}
        >
            <a href={"/docs/10-years-of-open-data"}>
                {stateShowBlog ?
                    <span>🗞️ Click <strong>here</strong> to read our blog!</span>
                    :
                    <span>🎂 <strong>10 Years</strong> of CERN Open Data!</span>
                }
            </a>
            <div id="confetti-holder"></div>
        </div>
    )
}

if (new Date() > unlock_date) {
    const titleContainer = document.getElementById("react-anniversary")
    ReactDOM.render(React.createElement(Celebrate), titleContainer)
}
