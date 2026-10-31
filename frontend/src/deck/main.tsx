import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MotionConfig } from "motion/react";
import "../styles.css";
import "./deck.css";
import { Deck } from "./Deck";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <MotionConfig reducedMotion="user">
      <Deck />
    </MotionConfig>
  </StrictMode>,
);
