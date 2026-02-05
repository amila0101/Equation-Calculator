import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./App.css";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { evaluate } from "mathjs";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

// API base URL: use env in production (Netlify), localhost when developing
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// Standard keypad layout
const keypadKeys = [
  "C",
  "⌫",
  "(",
  ")",
  "/",
  "7",
  "8",
  "9",
  "×",
  "4",
  "5",
  "6",
  "-",
  "1",
  "2",
  "3",
  "+",
  "0",
  ".",
  "=",
];

const scientificLabels = {
  asin: "sin⁻¹",
  acos: "cos⁻¹",
  atan: "tan⁻¹",
  sin: "sin",
  cos: "cos",
  tan: "tan",
  nPr: "nPr",
  nCr: "nCr",
  // ... add others if you want to change labels for log/ln etc.
};

// Scientific keys (insert functions/constants)
const sciKeys = ["sin", "cos", "tan", "asin" , "acos", "atan" ,"log", "ln", "√", "xʸ", "π", "e", "±", "%","x!", "nPr", "nCr"];

const superscriptMap = {
  '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
  '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
};

const defaultChartOptions = {
  responsive: true,
  scales: {
    x: {
      ticks: { color: "#94a3b8" },
      grid: { color: "rgba(148,163,184,0.2)" },
    },
    y: {
      ticks: { color: "#94a3b8" },
      grid: { color: "rgba(148,163,184,0.2)" },
    },
  },
  plugins: {
    legend: {
      labels: {
        color: "#e5e7eb",
      },
    },
  },
};

function App() {
  const [mode, setMode] = useState("symbolic");
  const [equation, setEquation] = useState("");
  const [variable, setVariable] = useState("x");
  const [type, setType] = useState("algebra");
  const [apiData, setApiData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [memory, setMemory] = useState(null);

  const addNormToInput = () => {
    let input = document.getElementById('equation-input');
    if (!input) {
      // Fallback: try to get input by class name
      const inputs = document.getElementsByClassName('equation-input');
      if (inputs.length === 0) return;
      input = inputs[0];
    }

    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;

    // Use the current 'equation' state variable
    const selectedText = equation.substring(start, end);
    const newText = equation.substring(0, start) + "||" + selectedText + "||" + equation.substring(end);

    setEquation(newText);

    // Set focus back to middle of bars after state update
    setTimeout(() => {
      const updatedInput = document.getElementById('equation-input') || document.getElementsByClassName('equation-input')[0];
      if (updatedInput) {
        updatedInput.focus();
        const newCursorPos = start + 2 + selectedText.length;
        updatedInput.setSelectionRange(newCursorPos, newCursorPos);
      }
    }, 10);
  };

  const activeType = mode === "arithmetic" ? "arithmetic" : type;
  const showVariableField = mode !== "arithmetic" && activeType !== "arithmetic";

  const handleModeChange = (nextMode) => {
    setMode(nextMode);
    setError("");
    setApiData(null);
    if (nextMode === "arithmetic") {
      setType("algebra");
      setVariable("x");
    }
  };

  const appendHistory = (payload) => {
    setHistory((prev) => [payload, ...prev].slice(0, 6));
  };

  const handleFindNorm = async (e) => {
    e.preventDefault();
    setError("");
    setApiData(null);

    if (!equation.trim()) {
      setError("Please enter a vector to find its norm (e.g., [3,4] or {4,3,0}).");
      return;
    }

    // Check if equation contains vector notation [a,b], {a,b}, or vector operations
    const hasVector = /\[[^\]]+\]/.test(equation) || /\{[^}]+\}/.test(equation);
    
    if (!hasVector) {
      setError("Please enter a vector in the format [a,b], {a,b}, or [a,b]+[c,d]");
      return;
    }

    // If not already wrapped with ||...||, wrap it
    let normEquation = equation.trim();
    const originalEquation = normEquation; // Store original for error recovery
    const alreadyWrapped = normEquation.startsWith("||") && normEquation.endsWith("||");
    
    if (!alreadyWrapped) {
      normEquation = "||" + normEquation + "||";
      // Update the input field visually
      setEquation(normEquation);
    }

    // Use the same processing as handleSubmit
    const superToNormal = (str) => {
      const map = {
        '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
        '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '⁹',
        '⁻': '-'
      };
      let cleaned = str.replace(/sin⁻¹/g, "asin")
                       .replace(/cos⁻¹/g, "acos")
                       .replace(/tan⁻¹/g, "atan");
      return cleaned.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]/g, (m) => map[m]);
    };

    let finalEq = normEquation.replace(/□/g, "");
    finalEq = superToNormal(finalEq);
    finalEq = finalEq.replace(/\^/g, "**")
                     .replace(/π/g, "pi")
                     .replace(/(\d)pi/g, "$1*pi")
                     .replace(/pi(\d)/g, "pi*$1")
                     .replace(/e/g, "e")
                     .replace(/(\d)e/g, "$1*e")
                     .replace(/e(\d)/g, "e*$1")
                     .replace(/(\d)!/g, "factorial($1)")
                     .replace(/%/g, "%")
                     .replace(/(\d+\.?\d*)%(\d+\.?\d*)/g, "($1/100)*$2")
                     .replace(/(\d+\.?\d*)%(?!\d)/g, "($1/100)")
                     .replace(/\s+/g, "");

    if (mode === "arithmetic") {
      finalEq = finalEq.replace(/[x×]/g, "*");
    } else {
      finalEq = finalEq.replace(/×/g, "*");
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/calc/solve`, {
        equation: finalEq,
        variable,
        type: activeType,
      });

      setApiData(response.data);
      appendHistory({
        id: Date.now(),
        equation: normEquation,
        type: activeType,
        resultPreview: summarizeResult(response.data.result),
        timestamp: new Date().toLocaleTimeString(),
      });
    } catch (err) {
      console.error(err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Something went wrong on the server.");
      // Restore original equation on error if we wrapped it
      if (!alreadyWrapped) {
        setEquation(originalEquation);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setError("");
    setApiData(null);

    const superToNormal = (str) => {
  const map = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '⁹',
    '⁻': '-' // Add this line!
  };
  // Replace trig labels first
  let cleaned = str.replace(/sin⁻¹/g, "asin")
                   .replace(/cos⁻¹/g, "acos")
                   .replace(/tan⁻¹/g, "atan");

  // Then replace any remaining superscripts
  return cleaned.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]/g, (m) => map[m]);

};

  // Clean the equation for the Python backend
    let finalEq = equation.replace(/□/g, "");
finalEq = superToNormal(finalEq);


  finalEq = finalEq
    .replace(/\^/g, "**")                      // Convert ^ to **
    .replace(/π/g, "pi")                       // Convert π to pi
    .replace(/(\d)pi/g, "$1*pi")
      .replace(/pi(\d)/g, "pi*$1")
      .replace(/e/g, "e")
      .replace(/(\d)e/g, "$1*e")
  .replace(/e(\d)/g, "e*$1")// 5pi -> 5*pi

  .replace(/(\d)!/g, "factorial($1)")
  ;

  finalEq = finalEq.replace(/%/g, "%");
  finalEq = finalEq.replace(/(\d+\.?\d*)%(\d+\.?\d*)/g, "($1/100)*$2");

// This converts "7%" into "7/100" (if no number follows)
 finalEq = finalEq.replace(/(\d+\.?\d*)%(?!\d)/g, "($1/100)");
 finalEq = finalEq.replace(/\s+/g, "");
 finalEq = finalEq.replace(/P/g, "P");
finalEq = finalEq.replace(/C/g, "C")
    finalEq = finalEq.replace(/(\d+)C(\d+)/g, "nCr($1,$2)");
finalEq = finalEq.replace(/(\d+)P(\d+)/g, "nPr($1,$2)");

     if (mode === "arithmetic") {
    finalEq = finalEq.replace(/[x×]/g, "*");
  }else {
      finalEq = finalEq.replace(/×/g, "*");
    }

if (!finalEq.trim()) {
    setError("Please enter an equation to solve.");
    return;
  }

    if (!equation.trim()) {
      setError("Please enter an equation to solve.");
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/calc/solve`, {
        equation:finalEq,
        variable,
        type: activeType,
      });
      setApiData(response.data);
      appendHistory({
        id: Date.now(),
        equation,
        type: activeType,
        resultPreview: summarizeResult(response.data.result),
        timestamp: new Date().toLocaleTimeString(),
      });
    } catch (err) {
      console.error(err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Something went wrong on the server.");
    } finally {
      setLoading(false);
    }
  }, [equation, variable, activeType, mode]);

  useEffect(() => {
    if (mode !== "symbolic" || type !== "algebra" || !apiData?.success) {
      setGraphData(null);
      return;
    }

    const data = buildGraphData(equation, variable);
    setGraphData(data);
  }, [mode, type, apiData, equation, variable]);

  const renderResultValue = () => {
    if (!apiData || !apiData.success) {
      return <span className="empty-state">Run a calculation to see results.</span>;
    }

    const { result } = apiData;
    if (result == null) {
      return <span className="empty-state">No result returned.</span>;
    }

    if (typeof result === "object") {
      return <pre className="result-pre">{JSON.stringify(result, null, 2)}</pre>;
    }

    return <span>{String(result)}</span>;
  };

  const renderSteps = () => {
    if (!apiData || !apiData.success) {
      return <p className="empty-state">Solve an equation to see the step-by-step explanation.</p>;
    }

    const steps = apiData.steps || [];
    if (!steps.length) {
      return <p className="empty-state">No steps were generated for this equation.</p>;
    }

    return (
      <ul className="steps-list">
        {steps.map((step, idx) => (
          <li key={idx}>{step}</li>
        ))}
      </ul>
    );
  };

  const renderHistory = () => {
    if (!history.length) {
      return <p className="empty-state">Your recent solves will appear here.</p>;
    }

    return (
      <ul className="history-list">
        {history.map((entry) => (
          <li key={entry.id} className="history-item">
            <div className="history-meta">
              <span>{entry.type.toUpperCase()}</span>
              <span>{entry.timestamp}</span>
            </div>
            <div className="history-equation">{entry.equation}</div>
            {entry.resultPreview && <div className="history-result">{entry.resultPreview}</div>}
          </li>
        ))}
      </ul>
    );
  };

  const insertToken = useCallback((key) => {
      if (key === "×" || key === "*") {
    setEquation((prev) => prev + "x");
    return;
  }

      if (["asin", "acos", "atan"].includes(key)) {
  const displayLabel = scientificLabels[key]; // e.g., "sin⁻¹"
  setEquation((prev) => prev + `${displayLabel}(`);
  return;
}

    // Handle scientific tokens
    if (["sin", "cos", "tan", "log", "ln"].includes(key)) {
      setEquation((prev) => prev + `${key}(`);
      return;
    }
    if (key === "√") {
      setEquation((prev) => prev + "sqrt(");
      return;
    }
    if (key === "π") {
      setEquation((prev) => prev + "π");
      return;
    }
    if (key === "e") {
      setEquation((prev) => prev + "e");
      return;
    }

    if (key === "xʸ") {
    setEquation((prev) => prev + "□");
    return;
  }

      if (/^[0-9]$/.test(key) && equation.endsWith("□")) {
    const superscriptDigit = superscriptMap[key] || key;
    setEquation((prev) => prev.slice(0, -1) + superscriptDigit);
    return;
  }

     if (key === "nPr") {
  setEquation((prev) => prev + "P");
  return;
}

     if (key === "nCr") {
  setEquation((prev) => prev + "C");
  return;
}

    if (key === "±") {
      setEquation((prev) => toggleSign(prev));
      return;
    }
    if (key === "%") {
      setEquation((prev) => prev + "%");
      return;
    }
    setEquation((prev) => prev + key);
  }, [equation]);

  const handleKeypadClick = useCallback((key) => {
    if (key === "C") {
      setEquation("");
      setApiData(null);
      setError("");
      return;
    }
    if (key === "⌫") {
      setEquation((prev) => prev.slice(0, -1));
      return;
    }
    if (key === "=") {
      // Trigger submit programmatically for arithmetic convenience
      const fakeEvent = { preventDefault: () => {} };
      handleSubmit(fakeEvent);
      return;
    }
    if (key === "M+") {
      setMemory(apiData?.result ?? (equation || "0"));
      return;
    }
    if (key === "MR") {
      if (memory != null) {
        setEquation((prev) => prev + String(memory));
      }
      return;
    }
    if (key === "MC") {
      setMemory(null);
      return;
    }

    if (key === "x!") {
    setEquation((prev) => prev + "!");
    return;
  }
    insertToken(key);
  }, [apiData?.result, equation, handleSubmit, memory, insertToken]);

  const keypad = useMemo(
    () => (
      <div className="keypad">
        {keypadKeys.map((key) => (
          <button type="button" key={key} onClick={() => handleKeypadClick(key)}>
            {key}
          </button>
        ))}
      </div>
    ),
    [handleKeypadClick]
  );

  const sciPad = useMemo(
    () => (
      <div className="keypad sci-pad">
        {["MC", "MR", "M+", ...sciKeys].map((key) => (
          <button type="button" key={key} onClick={() => handleKeypadClick(key)}>
            {/* Look up the label in our map; if not found, use the key itself */}
          {scientificLabels[key] || key}
          </button>
        ))}
      </div>
    ),
    [handleKeypadClick]
  );

  // Global keyboard support: numbers, operators, enter, backspace, escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      const key = e.key;

      // Allow typing inside text inputs as normal
      const activeTag = document.activeElement?.tagName;
      const isTypingInInput =
        activeTag === "INPUT" || activeTag === "TEXTAREA" || document.activeElement?.isContentEditable;
      if (isTypingInInput) return;

      if (/^[0-9]$/.test(key)) {
        handleKeypadClick(key);
        e.preventDefault();
        return;
      }

      if (["+", "-", "x", "/", "(", ")", "."].includes(key)) {
        handleKeypadClick(key);
        e.preventDefault();
        return;
      }

      if (key === "Enter" || key === "=") {
        handleKeypadClick("=");
        e.preventDefault();
        return;
      }

      if (key === "Backspace") {
        handleKeypadClick("⌫");
        e.preventDefault();
        return;
      }

      if (key === "Escape") {
        handleKeypadClick("C");
        e.preventDefault();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeypadClick]);

  return (
    <div className="app-root">
      <div className="app-shell">
        <header className="app-header">
          <div className="app-title">
            <h1>Equation Calculator</h1>
            <span>Solve algebra, calculus, trig, and arithmetic with clear steps.</span>
          </div>
          <div className="badge">React + FastAPI</div>
        </header>

        <div className="app-grid">
          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Input</div>
                <div className="card-subtitle">Describe your equation and what you want to solve.</div>
              </div>
              <div className="pill">{activeType.toUpperCase()}</div>
            </div>

            <div className="mode-tabs">
              <button
                type="button"
                className={`mode-tab ${mode === "symbolic" ? "active" : ""}`}
                onClick={() => handleModeChange("symbolic")}
              >
                Symbolic (Algebra / Calc / Trig)
              </button>
              <button
                type="button"
                className={`mode-tab ${mode === "arithmetic" ? "active" : ""}`}
                onClick={() => handleModeChange("arithmetic")}
              >
                Quick Arithmetic
              </button>
            </div>

            <form onSubmit={handleSubmit} className="form-grid">
              <div>
                <div className="field-label">Equation</div>
                <input
                  id="equation-input"
                  type="text"
                  className="equation-input"
                  placeholder={
                    mode === "arithmetic"
                      ? "e.g. 12/4 + 5*2 or [3,4]+[1,2]"
                      : "e.g. x**2 - 4, sin(x) - 1, x**3 + 2*x"
                  }
                  value={equation}
                  onChange={(e) => {
    // Automatically replace * with x as the user types
    const val = e.target.value.replace(/\*/g, "x");
    setEquation(val);
  }}
                />
                <div className="chip-row">
                  <span className="chip">Use ** for powers (x**2)</span>
                  <span className="chip">Functions: sin(x), cos(x), exp(x)...</span>
                  <button
    type="button"
    className="chip"
    onClick={addNormToInput}
    style={{ cursor: 'pointer', border: '1px solid #444' }}
  >
    Add Norm ||x||
  </button>
                </div>

                {mode === "arithmetic" && (
                  <>
                    {sciPad}
                    {keypad}
                  </>
                )}

              </div>

              {mode === "symbolic" && (
                <div className="field-row">
                  <div>
                    <div className="field-label">Type</div>
                    <select value={type} onChange={(e) => setType(e.target.value)} className="select">
                      <option value="algebra">Algebra</option>
                      <option value="calculus">Calculus</option>
                      <option value="trig">Trigonometry</option>
                    </select>
                  </div>

                  {showVariableField && (
                    <div>
                      <div className="field-label">Variable</div>
                      <input
                        type="text"
                        className="equation-input variable-input"
                        value={variable}
                        onChange={(e) => setVariable(e.target.value || "x")}
                      />
                    </div>
                  )}

                  <div style={{ marginLeft: "auto", display: "flex", gap: "10px" }}>
                    <div className="field-label">&nbsp;</div>
                    <button 
                      type="button" 
                      className="primary-button" 
                      onClick={handleFindNorm}
                      disabled={loading}
                      style={{ backgroundColor: "#3b82f6" }}
                    >
                      <span>||</span>
                      {loading ? "Computing..." : "Find Norm"}
                    </button>
                    <button type="submit" className="primary-button" disabled={loading}>
                      <span>⏵</span>
                      {loading ? "Solving..." : "Solve"}
                    </button>
                  </div>
                </div>
              )}

              {mode === "arithmetic" && (
                <div className="field-row" style={{ justifyContent: "space-between" }}>
                  <div className="memory-indicator">
                    Memory: {memory == null ? "—" : String(memory)}
                  </div>
                  <div style={{ display: "flex", gap: "10px" }}>
                    <button 
                      type="button" 
                      className="primary-button" 
                      onClick={handleFindNorm}
                      disabled={loading}
                      style={{ backgroundColor: "#3b82f6" }}
                    >
                      <span>||</span>
                      {loading ? "Computing..." : "Find Norm"}
                    </button>
                    <button type="submit" className="primary-button" disabled={loading}>
                      <span>⏵</span>
                      {loading ? "Solving..." : "Solve"}
                    </button>
                  </div>
                </div>
              )}

              <p className="helper-text">
                The request is sent to the API at{" "}
                <code>{API_BASE_URL}/api/calc/solve</code>.
              </p>

              {error && (
                <div className="error-banner">
                  <strong>Error:</strong> {error}
                </div>
              )}
            </form>
          </section>

          <section className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Result & Steps</div>
                <div className="card-subtitle">
                  See the final answer and a breakdown of how it was computed.
                </div>
              </div>
            </div>

            <div className="result-body">
              <div>
                <div className="result-label">Answer</div>
                <div className="answer-display">
                  {apiData && apiData.success ? summarizeResult(apiData.result) : "—"}
                </div>
              </div>

              <div>
                <div className="result-label">Detailed Result</div>
                <div className="result-block">{renderResultValue()}</div>
              </div>

              <div>
                <div className="result-label">Steps</div>
                <div className="result-block">{renderSteps()}</div>
              </div>

              <div className="chart-container">
                <div className="chart-title">Graph (Algebra only)</div>
                {graphData ? <Line data={graphData} options={defaultChartOptions} /> : (
                  <p className="chart-empty">Graph will appear after solving an algebraic expression.</p>
                )}
              </div>
            </div>
          </section>

          <section className="card history-card">
            <div className="card-header">
              <div>
                <div className="card-title">Recent History</div>
                <div className="card-subtitle">Track what you solved in this session.</div>
              </div>
            </div>
            {renderHistory()}
          </section>
        </div>
      </div>
    </div>
  );
}

function summarizeResult(result) {
  if (result == null) return "";
  if (Array.isArray(result)) {
    return result.slice(0, 3).join(", ");
  }
  if (typeof result === "object") {
    return JSON.stringify(result).slice(0, 80);
  }
  return String(result);
}

function toggleSign(expr) {
  if (!expr) return "-";
  // Toggle sign of the last number or parenthesized term
  const match = expr.match(/(.*?)(-?\d*\.?\d+)$|(.+)/);
  if (!match) return "-" + expr;
  const [, prefix, number] = match;
  if (!number) return "-" + expr;
  if (number.startsWith("-")) {
    return prefix + number.slice(1);
  }
  return prefix + "-" + number;
}

function buildGraphData(equation, variable) {
  if (!equation) return null;
  const sanitized = equation.split("=")[0].replace(/\*\*/g, "^");
  const varName = variable || "x";
  const labels = [];
  const data = [];

  for (let x = -10; x <= 10; x += 0.5) {
    labels.push(Number(x.toFixed(1)));
    try {
      const val = evaluate(sanitized, { [varName]: x });
      data.push(typeof val === "number" && Number.isFinite(val) ? val : null);
    } catch {
      data.push(null);
    }
  }

  if (!data.some((point) => point !== null)) {
    return null;
  }

  return {
    labels,
    datasets: [
      {
        label: `f(${varName}) = ${equation}`,
        data,
        borderColor: "#22d3ee",
        backgroundColor: "rgba(34, 211, 238, 0.2)",
        pointRadius: 0,
        tension: 0.25,
      },
    ],
  };
}

export default App;
